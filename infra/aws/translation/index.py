import boto3, hashlib, json, os, time

from botocore.exceptions import ClientError

translate = boto3.client('translate')
ddb = boto3.resource('dynamodb')
identity = ddb.Table(os.environ['IDENTITY_TABLE'])
cache = ddb.Table(os.environ['CACHE_TABLE'])
origin = os.environ['FRONTEND_ORIGIN'].rstrip('/')

# Anonymous UI translation is intentionally limited to text shipped by ReLiC.
# This prevents the public homepage endpoint from becoming a free arbitrary
# translation proxy. Authenticated roleplay uses /chat/translate instead.
UI_TEXT = {
    # Shared navigation / controls
    'About','Shaelvien','RIST','Game Now','Enter Shaelvien','Discover ReLiC','GAME NOW',
    'START','Exit','Back','World','Dice','Language','Video','Picture','Sound','Effects','Manage Storage','Account',
    'Stars','Sky','Calendar','UGC','Clock','Edit','Show SUM','Enabled','Disabled','Loading…',
    'Primary language','Private-game handling','System mechanics','Set percentage','GM typed response','Legibility %','Manual response',
    'Cloud Usage','View usage','Import Campaign','Import','Export Campaign','Export','Request Help',
    'Profile','Player Alias','Discord ID','Personal Details','Manage','Parental Controls','Email Preferences','Manage emails','Linked Accounts','Manage accounts','Help',
    'Exactly what the player should read',

    # Start/settings menu explanatory copy
    'Edit shared world context and display time.',
    'GameMaster table controls. Disabling SUM leaves the dice visible but requires players to add their own results.',
    "Common means ordinary human speech and is presented in each user's primary language. In-world languages still require a matching character language; Linguistics determines partial comprehension.",
    "System mechanics uses the character's language proficiency plus Linguistics. Percentage gives the GM direct control. Manual response lets the GM author exactly what the player receives.",
    'These controls affect private-game language resolution.',
    'Your character sheet languages and Linguistics determine what in-world speech you can read.',
    'Only the GameMaster can change this setting.','This setting applies to the table.',
    'Picture Mode','Brightness','Contrast','Gamma','Motion','Aspect','Exposure','Highlights','Shadows','Saturation','Temperature','Sharpness','Opacity',
    'Master','Music','Effects','Voice','Ambient','UI','Sound Apps','Future integrations','Particles','Weather','Lighting','Parallax / 3D','Animation',
    'Mixing-board foundation. Shaelvien tileset controls and external sound-app integrations can plug into these channels.',
    'Player image, alias and personal account details','Log in with Discord','Unavailable',

    # Homepage headings / calls to action
    'Build Worlds Together','Journey Beyond Your Campaign','Share Your Imagination','NOW ENTERING','Core Rule TTRPG · Persistent World','Powered by RIST',
    'The Studio','The Game · The World','The Platform','The Open Table','Your Game','A Shared Creative Ecosystem',
    'Multiple GameMasters. One Living World.','Artists Become Part of the Table','Accessible by Design. Inclusive by Default.','Play Across Devices.','Different Worlds Need Different Boundaries','A Business Built Around Participation',
    'Recursive Immersive Sandbox Table Top','A Core Rule TTRPG built for a world that can keep growing.','Use the tools without surrendering the table.',
    'The campaign is part of the world—not the edge of it.','The World Is Opening','Create something worth entering.',
    'AI transparency:','players','Built for','Donate with PayPal',

    # Homepage body copy. Strong-tag paragraphs are also represented by their
    # exact adjacent text-node fragments because browser localization operates
    # on rendered text nodes rather than rewriting HTML.
    'is a Core Rule TTRPG and persistent shared world.',
    'is the recursive tabletop technology beneath it—connecting world creation, roleplaying, tactical encounters, maps, cards, dice, miniatures, tokens, animated sprites, scenery, media, and persistent spaces without losing the freedom of the table.',
    'Friends & family testing is opening first as the world moves toward wider public testing.',
    'ReLiCGameMaster is creating a digital tabletop ecosystem where maps, dice, cards, miniatures, tokens, animated sprites, character sheets, terrain, scenery, worlds, rules, and stories can live in the same space while retaining the recognizable language of tabletop play.',
    'The ambition is larger than reproducing a physical table on a screen: give players somewhere to play and grow, GameMasters somewhere to create together, storytellers somewhere to build continuity, artists somewhere their work can become playable, and developers a foundation that can expand without forcing every game into the same shape.',
    "Shaelvien can be played as its own tabletop roleplaying game. In MMO Mode, its Core Rules become the shared world's enforced rules of play, allowing many players and GameMasters to participate without every table becoming a different reality. Characters, places, encounters, time, consequences, and progression can persist beyond a single session.",
    "RIST is the tabletop environment beneath Shaelvien: a recursive play and creation space for worlds within worlds, from global travel to tactical encounters and the objects inside a character's pack. Maps, tiles, cards, dice, miniatures, tokens, animated sprites, scenery, terrain, media, and player tools can all share one extensible table.",
    "Outside Shaelvien's MMO Mode, RIST is designed as a flexible tabletop studio rather than a mandatory rules engine. Build with its tools, bring a system your group already plays, create your own, or use the table as a foundation for board games, card games, tactical games, interactive media, and original worlds.",
    'RIST connects the people who build, run, illustrate, populate, and explore worlds while keeping authority, attribution, access, and ownership visible.',
    "GameMasters can collaborate instead of operating isolated tables: build neighboring regions, share campaigns, run simultaneous events, hand travelers between adventures, and contribute to the same persistent Shaelvien while permissions protect each creator's authority. A GM can remain a player in the greater world while still governing the places entrusted to them.",
    'A Shaelvien character is meant to build a history. Progress can follow the player beyond a single adventure as characters travel between compatible campaigns, GameMasters, regions, and communities. In MMO Mode, shared Core Rules and progression boundaries make that travel possible without one campaign casually rewriting the balance of another.',
    'Creators can offer tiles, miniatures, tokens, sprites, scenery, cards, maps, and other playable assets. Free contributions can retain visible creator attribution and, when provided, a donation or support link. Commercial creator offerings can be discovered where the artwork is actually used—not separated from the game experience.',
    'AI-generated or AI-assisted material should be identified clearly rather than presented as human-created artwork, while creator and license information follows third-party assets through the library.',
    'RIST is being designed so more people can reach the same table through different paths: scalable and readable interfaces, keyboard, touch and controller-friendly interaction, adaptable presentation, and support for players with visual, hearing, speech, or mobility needs. Accessibility changes how someone reaches and experiences the world—not whether they belong in it.',
    'Flexible character and worldbuilding tools avoid unnecessarily forcing identity, culture, body, or character concepts into assumptions inherited from a single game system.',
    'RIST is being built around a browser-first, device-flexible foundation so the same table can be reached from desktop computers, laptops, tablets, and phones without treating one device as the only proper way to play. Player interaction is being designed around mouse, keyboard, touch, and controller input, with layouts that adapt to the available screen rather than simply shrinking a desktop interface.',
    'The longer-term platform direction includes console-friendly play where platform requirements allow it, while keeping shared characters, worlds, campaigns, and tabletop state consistent across supported devices.',
    'Shared play does not mean every destination is appropriate for every player. Worlds, regions, campaigns, and experiences can use age and content-rating zones so access follows the audience a creator intended. This gives GameMasters room to tell different kinds of stories while creating clearer protections for younger players.',
    'ReLiCGameMaster is designed so revenue can come from the services that make a persistent ecosystem possible rather than turning player attention into the product. The developing model includes hosted and persistent world services, paid GameMaster sessions, creator asset sales, and optional ecosystem services—while free assets, creator donations, locally run tables, and user-owned content remain meaningful parts of RIST. Exact marketplace fees and revenue shares will be published when those programs are ready rather than promised before they are finalized.',
    'Built for',
    '· GameMasters · worldbuilders · artists · storytellers · developers · creators · different devices · different ways to play',
    'Shaelvien and RIST are moving through active development toward persistent testing, Kickstarter, and broader public access. Build a place, tell a story, create an asset, guide a campaign—or become someone whose journey continues beyond it.',
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
