import boto3, hashlib, json, os, time

from botocore.exceptions import ClientError

translate = boto3.client('translate')
ddb = boto3.resource('dynamodb')
identity = ddb.Table(os.environ['IDENTITY_TABLE'])
cache = ddb.Table(os.environ['CACHE_TABLE'])
origin = os.environ['FRONTEND_ORIGIN'].rstrip('/')

UI_TEXT = {
    # Shared / navigation
    'About','Shaelvien','RIST','Game Now','Enter Shaelvien','Discover ReLiC','GAME NOW',
    'The Studio','The Game · The World','The Platform','The Open Table','Your Game',
    'A Shared Creative Ecosystem','START','Exit','Back','World','Dice','Language','Video','Picture','Sound','Effects','Manage Storage','Account',
    'Stars','Sky','Calendar','UGC','Clock','Edit','Show SUM','Enabled','Disabled','Loading…',
    'Primary language','Private-game handling','System mechanics','Set percentage','GM typed response','Legibility %','Manual response',
    'Cloud Usage','View usage','Import Campaign','Import','Export Campaign','Export','Request Help',
    'Profile','Player Alias','Discord ID','Personal Details','Manage','Parental Controls','Email Preferences','Manage emails','Linked Accounts','Manage accounts','Help',
    'Build Worlds Together','Journey Beyond Your Campaign','Share Your Imagination','NOW ENTERING','Core Rule TTRPG · Persistent World','Powered by RIST',
    'Multiple GameMasters. One Living World.','Artists Become Part of the Table','Accessible by Design. Inclusive by Default.','Play Across Devices.','Different Worlds Need Different Boundaries',
    'Recursive Immersive Sandbox Table Top','A Core Rule TTRPG built for a world that can keep growing.','Use the tools without surrendering the table.',
    'The campaign is part of the world—not the edge of it.',
    'Common means ordinary human speech and is presented in each user’s primary language. In-world languages still require a matching character language; Linguistics determines partial comprehension.',
    'GameMaster table controls. Disabling SUM leaves the dice visible but requires players to add their own results.',
    'System mechanics uses the character’s language proficiency plus Linguistics. Percentage gives the GM direct control. Manual response lets the GM author exactly what the player receives.',
    'These controls affect private-game language resolution.',
    'Your character sheet languages and Linguistics determine what in-world speech you can read.',
    'Only the GameMaster can change this setting.','This setting applies to the table.',
    'Exactly what the player should read',
}


def response(status, body=None):
    return {
        'statusCode': status,
        'headers': {
            'access-control-allow-origin': origin,
            'access-control-allow-headers': 'authorization,content-type',
            'access-control-allow-methods': 'POST,OPTIONS',
            'cache-control': 'no-store',
            'content-type': 'application/json',
        },
        'body': '' if body is None else json.dumps(body, ensure_ascii=False, separators=(',', ':')),
    }


def request_body(event):
    try:
        return json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return {}


def auth(event):
    header = (event.get('headers') or {}).get('authorization', '')
    if not header.lower().startswith('bearer '):
        return None
    raw = header.split(' ', 1)[1].strip()
    digest = hashlib.sha256(raw.encode()).hexdigest()
    item = identity.get_item(Key={'pk': 'session#' + digest}).get('Item')
    if not item or int(item.get('expiresAt', 0)) <= int(time.time()):
        return None
    return {'userId': str(item['userId']), 'displayName': item.get('username', 'RIST user')}


def clean_code(value, allow_auto=False):
    code = str(value or '').strip()
    if allow_auto and code == 'auto':
        return code
    if not (2 <= len(code) <= 5) or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-' for c in code):
        raise ValueError('Invalid language code')
    return code


def cached_translate(text, source, target, ttl_days=90):
    if source == target:
        return {'text': text, 'sourceLanguageCode': source, 'targetLanguageCode': target, 'cached': True}
    digest = hashlib.sha256((source + '\0' + target + '\0' + text).encode('utf-8')).hexdigest()
    item = cache.get_item(Key={'pk': digest}).get('Item')
    now = int(time.time())
    if item and int(item.get('expiresAt', 0)) > now:
        return {
            'text': str(item.get('translatedText', text)),
            'sourceLanguageCode': str(item.get('sourceLanguageCode', source)),
            'targetLanguageCode': str(item.get('targetLanguageCode', target)),
            'cached': True,
        }
    result = translate.translate_text(Text=text, SourceLanguageCode=source, TargetLanguageCode=target)
    translated = result.get('TranslatedText', text)
    resolved_source = result.get('SourceLanguageCode', source)
    expires = now + ttl_days * 86400
    cache.put_item(Item={
        'pk': digest,
        'translatedText': translated,
        'sourceLanguageCode': resolved_source,
        'targetLanguageCode': target,
        'expiresAt': expires,
    })
    return {'text': translated, 'sourceLanguageCode': resolved_source, 'targetLanguageCode': target, 'cached': False}


def handler(event, context):
    method = event['requestContext']['http']['method']
    path = event.get('rawPath', '')
    if method == 'OPTIONS':
        return response(204)
    if method != 'POST':
        return response(405, {'error': 'Method not allowed'})

    req = request_body(event)
    try:
        target = clean_code(req.get('targetLanguageCode'))
        source = clean_code(req.get('sourceLanguageCode') or 'en', allow_auto=True)
    except ValueError as exc:
        return response(400, {'error': str(exc)})

    if path == '/ui/translate':
        values = req.get('texts') or []
        if not isinstance(values, list) or not values or len(values) > 80:
            return response(400, {'error': 'texts must contain 1-80 UI strings'})
        output = []
        for value in values:
            text = str(value or '').strip()
            if not text or text not in UI_TEXT:
                output.append({'source': text, 'text': text, 'translated': False})
                continue
            if len(text.encode('utf-8')) > 9000:
                output.append({'source': text, 'text': text, 'translated': False})
                continue
            try:
                item = cached_translate(text, source, target, ttl_days=365)
                output.append({'source': text, **item, 'translated': True})
            except ClientError:
                output.append({'source': text, 'text': text, 'translated': False})
        return response(200, {'items': output})

    if path == '/chat/translate':
        session = auth(event)
        if not session:
            return response(401, {'error': 'Authentication required'})
        text = str(req.get('text') or '')
        if not text.strip() or len(text) > 1200 or len(text.encode('utf-8')) > 9000:
            return response(400, {'error': 'Chat text must contain 1-1200 characters'})
        try:
            result = cached_translate(text, source, target, ttl_days=90)
            return response(200, result)
        except translate.exceptions.UnsupportedLanguagePairException:
            return response(400, {'error': 'Unsupported language pair'})
        except ClientError:
            return response(502, {'error': 'Translation service unavailable'})

    return response(404, {'error': 'Not found'})
