from botocore.exceptions import ClientError

from index import (
    auth,
    cached_translate,
    clean_code,
    handler as legacy_handler,
    request_body,
    response,
    translate,
)


def _authenticated_ui_translate(event):
    """Translate arbitrary interface text only for an authenticated RIST session.

    Anonymous callers retain the strict shipped-string allowlist in index.handler.
    This keeps the public endpoint from becoming an open translation proxy while
    allowing the authenticated application shell to localize newly rendered UI.
    """
    session = auth(event)
    if not session:
        return None

    req = request_body(event)
    try:
        target = clean_code(req.get('targetLanguageCode'))
        source = clean_code(req.get('sourceLanguageCode') or 'en', allow_auto=True)
    except ValueError as exc:
        return response(400, {'error': str(exc)})

    values = req.get('texts') or []
    if not isinstance(values, list) or not values or len(values) > 80:
        return response(400, {'error': 'texts must contain 1-80 UI strings'})

    output = []
    total_bytes = 0
    for value in values:
        text = str(value or '').strip()
        encoded = len(text.encode('utf-8'))
        total_bytes += encoded
        if not text or encoded > 9000 or total_bytes > 120000:
            output.append({'source': text, 'text': text, 'translated': False})
            continue
        try:
            item = cached_translate(text, source, target, ttl_days=365)
            output.append({'source': text, **item, 'translated': True})
        except translate.exceptions.UnsupportedLanguagePairException:
            output.append({'source': text, 'text': text, 'translated': False, 'error': 'Unsupported language pair'})
        except ClientError:
            output.append({'source': text, 'text': text, 'translated': False})

    return response(200, {'items': output, 'authenticated': True})


def handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')
    if method == 'POST' and path == '/ui/translate':
        authenticated = _authenticated_ui_translate(event)
        if authenticated is not None:
            return authenticated
    return legacy_handler(event, context)
