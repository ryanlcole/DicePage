import base64
import boto3
import email
import json
import os
import re
import secrets
import time
from email.message import EmailMessage
from email.policy import default
from urllib.parse import urlparse

s3 = boto3.client('s3')
ses = boto3.client('sesv2')
kms = boto3.client('kms')
ddb = boto3.client('dynamodb')

BUCKET = os.environ['MAIL_BUCKET']
TABLE = os.environ['TICKET_TABLE']
KMS_KEY_ID = os.environ['KMS_KEY_ID']
SUPPORT_GMAIL = os.environ['SUPPORT_GMAIL'].lower()
SUPPORT_ADDRESS = os.environ.get('SUPPORT_ADDRESS', 'query@relicgamemaster.com').lower()
MAIL_FROM = os.environ.get('MAIL_FROM', SUPPORT_ADDRESS)
RETENTION_SECONDS = int(os.environ.get('RETENTION_SECONDS', '2592000'))
PREFIX = os.environ.get('MAIL_PREFIX', 'raw/')

TICKET_RE = re.compile(r'\[ReLiC\s+#([A-Z0-9]{12,32})\]', re.I)
EMAIL_RE = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
NINE_DIGIT_RE = re.compile(r'(?<!\d)(?:\d[\s.\-()]*){9}(?!\d)')
DATE_RES = [
    re.compile(r'\b(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])\b'),
    re.compile(r'\b(?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])[-/.](?:\d{2}|\d{4})\b'),
    re.compile(r'(?i)\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{2,4})?\b'),
]
STREET_RE = re.compile(r'(?i)\b\d{1,6}\s+[A-Z0-9][A-Z0-9 .\'-]{1,50}\s+(?:street|st|road|rd|avenue|ave|boulevard|blvd|lane|ln|drive|dr|court|ct|way|highway|hwy|parkway|pkwy)\b\.?')
URL_RE = re.compile(r'https?://[^\s<>"\']+', re.I)
DANGEROUS_EXTENSIONS = {'.exe','.dll','.js','.jse','.vbs','.vbe','.scr','.cmd','.bat','.com','.ps1','.msi','.jar','.hta','.iso','.img','.lnk','.reg','.cpl','.wsf','.wsh','.svg'}

ONES = {
    'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,
    'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19
}
TENS = {'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60,'seventy':70,'eighty':80,'ninety':90}
SCALES = {'hundred':100,'thousand':1000,'million':1000000,'billion':1000000000}
NUMBER_WORD_RE = re.compile(r'(?i)\b(?:(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|and)[\s-]+){2,}(?:zero|one|two|three|four|five|six|seven|eight|nine|hundred|thousand|million|billion)\b')


def _number_words_value(text):
    words = re.findall(r'[a-z]+', text.lower())
    total = current = 0
    saw = False
    for word in words:
        if word == 'and':
            continue
        if word in ONES:
            current += ONES[word]; saw = True
        elif word in TENS:
            current += TENS[word]; saw = True
        elif word == 'hundred':
            current = max(current, 1) * 100; saw = True
        elif word in ('thousand','million','billion'):
            scale = SCALES[word]
            total += max(current, 1) * scale
            current = 0; saw = True
        else:
            return None
    return total + current if saw else None


def redact(text):
    if not text:
        return ''
    text = EMAIL_RE.sub('[REDACTED ADDRESS]', text)
    text = STREET_RE.sub('[REDACTED ADDRESS]', text)
    text = NINE_DIGIT_RE.sub('[REDACTED 9-DIGIT NUMBER]', text)
    for rx in DATE_RES:
        text = rx.sub('[REDACTED DATE]', text)
    def words_repl(match):
        value = _number_words_value(match.group(0))
        return '[REDACTED 9-DIGIT NUMBER]' if value is not None and 100000000 <= value <= 999999999 else match.group(0)
    text = NUMBER_WORD_RE.sub(words_repl, text)
    return text


def _safe_filename(name):
    name = os.path.basename(name or 'attachment.bin')
    return re.sub(r'[^A-Za-z0-9._ -]', '_', name)[:120]


def _extract_text_and_attachments(msg):
    text_parts = []
    attachments = []
    for part in msg.walk():
        ctype = part.get_content_type()
        disp = part.get_content_disposition()
        filename = part.get_filename()
        if disp == 'attachment' or filename:
            safe_name = _safe_filename(filename)
            ext = os.path.splitext(safe_name.lower())[1]
            payload = part.get_payload(decode=True) or b''
            if ext in DANGEROUS_EXTENSIONS or len(payload) > 8 * 1024 * 1024:
                raise ValueError('disallowed_attachment')
            attachments.append((safe_name, ctype, payload))
            continue
        if ctype == 'text/plain':
            try:
                text_parts.append(part.get_content())
            except Exception:
                payload = part.get_payload(decode=True) or b''
                text_parts.append(payload.decode(part.get_content_charset() or 'utf-8', errors='replace'))
    return '\n\n'.join(text_parts).strip(), attachments


def _verdict_ok(receipt):
    verdicts = receipt.get('receipt', {}) if 'receipt' in receipt else receipt
    for key in ('spamVerdict','virusVerdict','spfVerdict','dkimVerdict','dmarcVerdict'):
        status = (verdicts.get(key) or {}).get('status')
        if status and status not in ('PASS','GRAY'):
            return False, key + ':' + status
    return True, 'pass'


def _ticket():
    return secrets.token_hex(8).upper()


def _encrypt_text(value):
    result = kms.encrypt(KeyId=KMS_KEY_ID, Plaintext=value.encode('utf-8'), EncryptionContext={'purpose':'relic-support-ticket'})
    return base64.b64encode(result['CiphertextBlob']).decode('ascii')


def _decrypt_text(value):
    result = kms.decrypt(CiphertextBlob=base64.b64decode(value), EncryptionContext={'purpose':'relic-support-ticket'})
    return result['Plaintext'].decode('utf-8')


def _put_ticket(ticket, sender, source_key, subject):
    now = int(time.time())
    ddb.put_item(TableName=TABLE, Item={
        'ticket': {'S': ticket},
        'senderCipher': {'S': _encrypt_text(sender)},
        'sourceKey': {'S': source_key},
        'subject': {'S': redact(subject)[:300]},
        'createdAt': {'N': str(now)},
        'expiresAt': {'N': str(now + RETENTION_SECONDS)},
        'status': {'S': 'open'},
    }, ConditionExpression='attribute_not_exists(ticket)')


def _get_ticket(ticket):
    out = ddb.get_item(TableName=TABLE, Key={'ticket': {'S': ticket}}, ConsistentRead=True)
    item = out.get('Item')
    if not item or item.get('status',{}).get('S') != 'open' or int(item.get('expiresAt',{}).get('N','0')) <= int(time.time()):
        return None
    return item


def _send_raw(message):
    ses.send_email(FromEmailAddress=MAIL_FROM, Destination={'ToAddresses':[message['To']]}, Content={'Raw': {'Data': message.as_bytes()}})


def _forward_to_support(ticket, original_subject, body, attachments, received_at):
    out = EmailMessage()
    out['From'] = MAIL_FROM
    out['To'] = SUPPORT_GMAIL
    out['Reply-To'] = SUPPORT_ADDRESS
    out['Subject'] = f'[ReLiC #{ticket}] {redact(original_subject)[:180]}'
    out.set_content(
        f'ReLiC support ticket: {ticket}\n'
        f'Received: {received_at}\n\n'
        f'{redact(body)}\n\n'
        'Reply normally. Keep the [ReLiC #...] ticket code in the subject.'
    )
    for filename, ctype, payload in attachments:
        maintype, subtype = (ctype.split('/',1) + ['octet-stream'])[:2]
        out.add_attachment(payload, maintype=maintype, subtype=subtype, filename=redact(filename))
    _send_raw(out)


def _relay_support_reply(ticket, msg, body, attachments):
    item = _get_ticket(ticket)
    if not item:
        raise ValueError('invalid_or_expired_ticket')
    recipient = _decrypt_text(item['senderCipher']['S'])
    out = EmailMessage()
    out['From'] = MAIL_FROM
    out['To'] = recipient
    out['Reply-To'] = SUPPORT_ADDRESS
    out['Subject'] = f'[ReLiC #{ticket}] Support reply'
    out.set_content(redact(body))
    for filename, ctype, payload in attachments:
        maintype, subtype = (ctype.split('/',1) + ['octet-stream'])[:2]
        out.add_attachment(payload, maintype=maintype, subtype=subtype, filename=redact(filename))
    _send_raw(out)


def _delete_source(key, reason):
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
    finally:
        print(json.dumps({'event':'mail_destroyed','reason':reason,'ts':int(time.time())}))


def lambda_handler(event, context):
    records = event.get('Records', [])
    if not records:
        return {'ok': True, 'handled': 0}
    handled = 0
    for record in records:
        ses_record = record.get('ses', {})
        mail = ses_record.get('mail', {})
        message_id = mail.get('messageId')
        if not message_id:
            continue
        key = PREFIX + message_id
        ok, verdict_reason = _verdict_ok(ses_record)
        if not ok:
            _delete_source(key, verdict_reason)
            continue
        try:
            raw = s3.get_object(Bucket=BUCKET, Key=key)['Body'].read()
            msg = email.message_from_bytes(raw, policy=default)
            sender = email.utils.parseaddr(msg.get('From',''))[1].lower()
            recipients = [email.utils.parseaddr(x)[1].lower() for x in (msg.get_all('To',[]) or [])]
            if not sender or SUPPORT_ADDRESS not in ','.join(recipients):
                raise ValueError('invalid_sender_or_recipient')
            subject = msg.get('Subject','')
            body, attachments = _extract_text_and_attachments(msg)
            received_at = mail.get('timestamp') or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            ticket_match = TICKET_RE.search(subject)
            if sender == SUPPORT_GMAIL and ticket_match:
                _relay_support_reply(ticket_match.group(1).upper(), msg, body, attachments)
                _delete_source(key, 'support_reply_relayed')
            else:
                ticket = _ticket()
                _put_ticket(ticket, sender, key, subject)
                _forward_to_support(ticket, subject, body, attachments, received_at)
                s3.put_object_tagging(Bucket=BUCKET, Key=key, Tagging={'TagSet':[{'Key':'accepted','Value':'true'}]})
            handled += 1
        except Exception as exc:
            _delete_source(key, type(exc).__name__ + ':' + str(exc)[:120])
    return {'ok': True, 'handled': handled}
