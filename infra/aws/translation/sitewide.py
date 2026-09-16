import re

from botocore.exceptions import ClientError

from index import (
    UI_TEXT,
    auth,
    cached_translate,
    clean_code,
    handler as legacy_handler,
    request_body,
    response,
    translate,
)


# 000071.python.sitewide.line17.comment Static interface strings rendered by the public site and launcher but not yet
# 000072.python.sitewide.line18.comment represented in the older anonymous UI catalog. Keeping these explicit preserves
# 000073.python.sitewide.line19.comment the endpoint's original security boundary: anonymous callers may translate only
# 000074.python.sitewide.line20.comment text that ships with ReLiC/RIST.
PUBLIC_UI_EXTRA = {
    # 000075.python.sitewide.line22.comment Public-site navigation / story strip
    'Store',
    'Remember',
    'exist',
    'Live',
    'imagine',
    'Create',

    # 000076.python.sitewide.line30.comment Public Play entry / Discord handoff shell
    'Shaelvien startup',
    'Shaelvien entry options',
    'BUILD THE WORLD. THEN STEP INSIDE IT.',
    'SIGN IN',
    'SIGN UP',
    'RIST MMO / Sandbox · Public Alpha',
    'Account service configuration is unavailable.',
    'Account service configuration is incomplete.',
    'Your account could not be checked.',
    'Your account could not be prepared.',
    'Account storage is unavailable.',
    'Entering Shaelvien…',
    'Opening secure Discord sign up…',
    'Opening secure Discord sign in…',
    'Unable to start authentication.',
    'Completing secure Discord sign in…',
    'The sign-in handoff expired. Please try again.',
    'The account service returned an invalid session.',
    'Your authenticated session could not be verified.',
    'Authentication could not be completed.',

    # 000077.python.sitewide.line52.comment Launcher hero / device setup
    'A LIVING WORLD AWAITS',
    'BUILD THE WORLD.',
    'THEN STEP INSIDE IT.',
    'ENABLE MOTION & TILT',
    'Enabled for this browser session',
    'Permission denied — tap to try again',
    'Not available on this device',
    'Enable device movement for layered world depth',
    'ENTER SHAELVIEN',

    # 000078.python.sitewide.line63.comment Launcher primary cards
    'ACCESSIBILITY SHELL',
    'Screen reader, keyboard, switch, speech and coordinate access to the same world.',
    'ROLEPLAY',
    'Characters, dice, encounters and play.',
    'GAMEMASTER',
    'Build, manage and run campaigns.',
    'WORLDBUILDER',
    'Build the world map, tiers and layers.',
    'Choose, create or import a world first.',
    'IMMERSIONBUILDER',
    'Build parallax, AR, spatial audio, high-resolution assets and haptics.',
    'REGIONDEFINER',
    'Define regions from published world tiles.',
    'CAMPAIGNS',
    'Plan and organize campaigns for this world.',
    'TABLETOP',
    'Arrange the playable tabletop and campaign space.',
    'INSTANCE',
    'Enter local and encounter-scale instances.',
    'WEATHER',
    'Build and apply weather systems.',
    'GEOLOGICAL EVENTS',
    'Shape geological and world-scale events.',
    'ASTROLOGY',
    'Define celestial influence and world interpretation.',
    'HISTORY',
    'Record eras, events and world chronology.',
    'LORE',
    "Organize this world's setting knowledge and canon.",
    'ASTRONOMY',
    'Define stars, skies and celestial structure.',
    'RULEBOOKS',
    'Open systems, rules and reference books.',
    'ASSET DESIGNER',
    'Create tiles, tokens, sprites and other assets.',
    'CARD INDEX',
    'Your cards, library, store and custom card creator.',
    'DICE & TOOLS',
    'Open dice, cards and play tools.',

    # 000079.python.sitewide.line104.comment Launcher quick access / settings
    'CHARACTERS',
    'STORE',
    'FEEDBACK',
    'SETTINGS',
    'DEVICE',
    'MOTION & TILT',
    'GRAPHICS',
    'EXIT FULL SCREEN',
    'FULL SCREEN',
    'Return to browser window',
    'Use the maximum available display area',
    'This browser does not expose programmable full screen. Platform/browser display controls may still provide it.',
    'PARALLAX ON',
    'PARALLAX OFF',
    'Device parallax is enabled',
    'Device parallax is disabled',
    'Parallax controls are not available in this browser',
    'ACCESSIBILITY STATEMENT',
    '← BACK',
    'BUILT WITH ReLiC',
    'MORE THAN A GAME. A PLACE TO BELONG.',
    '● ONLINE · PUBLIC ALPHA',
}

# 000080.python.sitewide.line129.comment These are product/world identities, not ordinary interface vocabulary. They are
# 000081.python.sitewide.line130.comment never translated, even when embedded inside otherwise translatable UI copy.
BRAND_TERMS = (
    'ReLiCGameMaster.com',
    'ReLiCGameMaster',
    'SHAELVIEN',
    'Shaelvien',
    'SHAEP',
    'RIST',
    'ReLiC',
)
BRAND_ONLY = {value.casefold() for value in BRAND_TERMS}
_BRAND_RE = re.compile('|'.join(re.escape(value) for value in sorted(BRAND_TERMS, key=len, reverse=True)), re.IGNORECASE)


def _safe_cached_translate(text, source, target, ttl_days=365):
    """Translate presentation text while preserving Shaelvien/ReLiC identities.

    Protected placeholders intentionally change the translation-cache key, so any
    older cached result that incorrectly translated a brand term (for example RIST
    becoming a normal-language word) is bypassed rather than reused.
    """
    if text.casefold() in BRAND_ONLY:
        return {
            'text': text,
            'sourceLanguageCode': source,
            'targetLanguageCode': target,
            'cached': True,
        }

    replacements = []

    def protect(match):
        token = f'ZXQBRAND{len(replacements)}QXZ'
        replacements.append((token, match.group(0)))
        return token

    protected = _BRAND_RE.sub(protect, text)
    item = cached_translate(protected, source, target, ttl_days=ttl_days)
    translated = str(item.get('text', protected))

    for token, original in replacements:
        if token not in translated:
            # 000082.python.sitewide.line172.comment Failing closed is safer than allowing translation to mutate canon.
            return {
                **item,
                'text': text,
                'brandProtectionFallback': True,
            }
        translated = translated.replace(token, original)

    return {**item, 'text': translated}


def _translate_items(values, source, target, *, allow_arbitrary=False):
    output = []
    total_bytes = 0
    anonymous_allowed = UI_TEXT | PUBLIC_UI_EXTRA

    for value in values:
        text = str(value or '').strip()
        encoded = len(text.encode('utf-8'))
        total_bytes += encoded

        if not text or encoded > 9000 or total_bytes > 120000:
            output.append({'source': text, 'text': text, 'translated': False})
            continue

        if not allow_arbitrary and text not in anonymous_allowed and text.casefold() not in BRAND_ONLY:
            output.append({'source': text, 'text': text, 'translated': False})
            continue

        try:
            item = _safe_cached_translate(text, source, target, ttl_days=365)
            output.append({'source': text, **item, 'translated': True})
        except translate.exceptions.UnsupportedLanguagePairException:
            output.append({'source': text, 'text': text, 'translated': False, 'error': 'Unsupported language pair'})
        except ClientError:
            output.append({'source': text, 'text': text, 'translated': False})

    return output


def _validated_ui_request(event):
    req = request_body(event)
    try:
        target = clean_code(req.get('targetLanguageCode'))
        source = clean_code(req.get('sourceLanguageCode') or 'en', allow_auto=True)
    except ValueError as exc:
        return None, None, None, response(400, {'error': str(exc)})

    values = req.get('texts') or []
    if not isinstance(values, list) or not values or len(values) > 80:
        return None, None, None, response(400, {'error': 'texts must contain 1-80 UI strings'})

    return values, source, target, None


def _authenticated_ui_translate(event):
    """Translate arbitrary application-interface text for an authenticated session."""
    session = auth(event)
    if not session:
        return None

    values, source, target, error = _validated_ui_request(event)
    if error:
        return error

    return response(200, {
        'items': _translate_items(values, source, target, allow_arbitrary=True),
        'authenticated': True,
    })


def _anonymous_ui_translate(event):
    """Translate only shipped public/launcher strings before authentication."""
    values, source, target, error = _validated_ui_request(event)
    if error:
        return error

    return response(200, {
        'items': _translate_items(values, source, target, allow_arbitrary=False),
    })


def handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')

    if method == 'POST' and path == '/ui/translate':
        authenticated = _authenticated_ui_translate(event)
        if authenticated is not None:
            return authenticated
        return _anonymous_ui_translate(event)

    return legacy_handler(event, context)
