"""Disposable loopback fixture. NEVER deploy this directory.

Runs the unmodified production auth/authority handlers using Moto AWS storage.
Only the OAuth ceremony is replaced by out-of-band session fixtures. All HTTP
private API requests still traverse the real token and permission checks.
"""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
import mimetypes
import os
from pathlib import Path
import secrets
import sys
import threading
import time
import types
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / '.e2e-runtime'
WWWROOT = RUNTIME / 'publish' / 'wwwroot'


def require_test_environment(env=None, host='127.0.0.1', build_configuration='Debug'):
    env = os.environ if env is None else env
    # Independent gates, evaluated before importing AWS libraries or opening sockets.
    if (env.get('SHAELVIEN_TEST_AUTH') != '1'
            or env.get('SHAELVIEN_ENVIRONMENT') != 'test'
            or env.get('DOTNET_ENVIRONMENT') != 'Development'
            or env.get('NODE_ENV') != 'test'
            or host != '127.0.0.1'
            or build_configuration != 'Debug'):
        raise RuntimeError('Test harness refused: explicit local test environment required')


def write_private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LocalS3:
    """Loopback transport for presigned storage, not an API auth substitute.

    Uses SDK-generated policy/signature fields unchanged. Each capability is
    recorded out-of-band when the real handler generates it; changed fields,
    keys, expired capabilities and unsigned access are rejected by the server.
    Moto stores bytes, but does not prove AWS's real SigV4 implementation.
    """
    def __init__(self, client, base):
        self.client, self.base, self.capabilities = client, base, {}

    def __getattr__(self, name):
        return getattr(self.client, name)

    def generate_presigned_url(self, operation, Params, ExpiresIn=300, **kwargs):
        if operation != 'get_object':
            raise ValueError('Only download transport supported')
        ticket = secrets.token_urlsafe(32)
        self.capabilities[ticket] = ('GET', copy.deepcopy(Params), time.time() + ExpiresIn)
        return self.base + '/objects/' + ticket

    def generate_presigned_post(self, **kwargs):
        post = self.client.generate_presigned_post(**kwargs)
        ticket = secrets.token_urlsafe(32)
        self.capabilities[ticket] = ('POST', copy.deepcopy(kwargs), time.time() + kwargs.get('ExpiresIn', 300), copy.deepcopy(post['fields']))
        return {'url': self.base + '/objects/' + ticket, 'fields': post['fields']}


class Runtime:
    def __init__(self, base='http://127.0.0.1:8765'):
        require_test_environment()
        if urllib.parse.urlsplit(base).hostname != '127.0.0.1':
            raise RuntimeError('Non-loopback origin refused')
        # Moto never obtains production credentials. Every resource is in-memory.
        os.environ.update(AWS_ACCESS_KEY_ID='testing', AWS_SECRET_ACCESS_KEY='testing',
                          AWS_SESSION_TOKEN='testing', AWS_DEFAULT_REGION='us-east-1',
                          AWS_EC2_METADATA_DISABLED='true')
        from moto import mock_aws
        self.mock = mock_aws()
        self.mock.start()
        import boto3
        self.base = base
        self.ddb = boto3.resource('dynamodb', region_name='us-east-1')
        table_keys = {'IDENTITY_TABLE': ['pk'], **{k: ['pk', 'sk'] for k in (
            'USERS_TABLE', 'WORLD_TABLE', 'MEMBERSHIPS_TABLE', 'AUDIT_TABLE',
            'REALTIME_TABLE', 'AI_STATE_TABLE', 'TELEMETRY_TABLE')}}
        for variable, keys in table_keys.items():
            name = 'e2e-' + variable.lower()
            self.ddb.create_table(TableName=name, BillingMode='PAY_PER_REQUEST',
                KeySchema=[{'AttributeName': k, 'KeyType': 'HASH' if i == 0 else 'RANGE'} for i, k in enumerate(keys)],
                AttributeDefinitions=[{'AttributeName': k, 'AttributeType': 'S'} for k in keys])
            os.environ[variable] = name
        self.s3 = boto3.client('s3', region_name='us-east-1')
        self.s3.create_bucket(Bucket='e2e-private')
        self.s3.create_bucket(Bucket='e2e-public')
        os.environ.update(USER_DATA_BUCKET='e2e-private', STORAGE_BUCKET='e2e-private',
            USER_DATA_KEY_ARN='e2e-key', OWNER_USER_ID='e2e-platform-owner',
            FRONTEND_ORIGIN=base, FRONTEND_URL=base + '/Play/index.html',
            MCP_OAUTH_RETURN_URL=base + '/oauth/identity', SESSION_HOURS='1',
            PUBLIC_ASSET_BUCKET='e2e-public', DISCORD_CLIENT_ID='e2e-unused',
            DISCORD_SECRET_ARN='e2e-unused', TELEMETRY_SALT_SECRET_ARN='e2e-unused')
        boto3.client('secretsmanager').create_secret(Name='e2e-unused', SecretString='disposable-telemetry-salt')
        authority_dir = ROOT / 'infra/aws/rist-platform-authority'
        sys.path.insert(0, str(authority_dir))
        self.authority = load_module('e2e_authority', authority_dir / 'app.py')
        template = (ROOT / 'infra/aws/rist-discord-storage.yml').read_text()
        inline = template.split('      InlineCode: |\n', 1)[1].split('\nOutputs:', 1)[0]
        source = '\n'.join(line[8:] if line.startswith('        ') else line for line in inline.splitlines())
        self.auth = types.ModuleType('e2e_auth')
        exec(compile(source, 'rist-discord-storage.yml:InlineCode', 'exec'), self.auth.__dict__)
        self.transport = LocalS3(self.s3, base)
        self.auth.s3 = self.transport
        self.authority.s3 = self.transport
        self.sessions = {}
        for persona in ('user', 'gm'):
            uid = 'e2e-' + persona
            expiry = int(time.time()) + 900
            token = secrets.token_urlsafe(48)
            self.auth.ddb.put_item(Item={'pk': 'session#' + hashlib.sha256(token.encode()).hexdigest(),
                'userId': uid, 'username': 'AINPC E2E ' + persona, 'provider': 'discord', 'expiresAt': expiry})
            self.sessions[persona] = {'origin': base, 'token': token, 'provider': 'discord',
                'expiresAt': expiry, 'userId': uid}
            profile = {'AccountId': uid + '-account', 'PlayerAlias': 'AINPC E2E ' + persona,
                'Plan': 'gm-player' if persona == 'gm' else 'player',
                'CreatedAtUtc': '2026-01-01T00:00:00Z', 'AgeAtSignup': 30,
                'TermsAcceptedAtUtc': '2026-01-01T00:00:00Z', 'TermsVersion': '2026-08-30'}
            self.s3.put_object(Bucket='e2e-private', Key='users/' + uid + '/account/profile.json',
                               Body=json.dumps(profile).encode(), ContentType='application/json')
            self.authority.users.put_item(Item={'pk': 'USER#' + uid, 'sk': 'PROFILE',
                'worldSlots': 3, 'entitlements': ['access.gamemaster'] if persona == 'gm' else []})
            self.authority.memberships.put_item(Item={'pk': 'WORLD#e2e-shared', 'sk': 'USER#' + uid,
                'worldId': 'e2e-shared', 'userId': uid, 'role': 'GM' if persona == 'gm' else 'PC'})

    def close(self):
        self.mock.stop()

    def dispatch(self, service, method, path, token='', payload=None):
        parsed = urllib.parse.urlsplit(path)
        event = {'requestContext': {'http': {'method': method, 'sourceIp': '127.0.0.1'}, 'domainName': '127.0.0.1'},
                 'rawPath': parsed.path, 'headers': {'authorization': 'Bearer ' + token} if token else {},
                 'queryStringParameters': dict(urllib.parse.parse_qsl(parsed.query)),
                 'body': json.dumps(payload) if payload is not None else ''}
        return (self.auth if service == 'auth' else self.authority).handler(event, None)


def make_handler(runtime):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # URLs may contain normal one-time handoff/storage capabilities.

        def send(self, status, payload=b'', content_type='application/json', headers=None):
            if isinstance(payload, str):
                payload = payload.encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            for key, value in (headers or {}).items():
                if key.lower() not in ('content-type', 'content-length', 'cache-control'):
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)

        def handle_request(self):
            # Reject DNS rebinding and cross-origin browser writes even on loopback.
            if self.headers.get('Host') != urllib.parse.urlsplit(runtime.base).netloc:
                return self.send(403, '{}')
            origin = self.headers.get('Origin')
            if origin and origin != runtime.base:
                return self.send(403, '{}')
            parsed = urllib.parse.urlsplit(self.path)
            path = urllib.parse.unquote(parsed.path)
            if self.command == 'OPTIONS':
                return self.send(204)
            if path.startswith('/api/'):
                service = 'auth' if path.startswith('/api/auth/') else 'authority'
                prefix = '/api/' + service
                route = self.path[len(prefix):]
                raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                payload = json.loads(raw) if raw else None
                header = self.headers.get('Authorization', '')
                token = header[7:] if header.lower().startswith('bearer ') else ''
                result = runtime.dispatch(service, self.command, route, token, payload)
                return self.send(result['statusCode'], result.get('body', ''), headers=result.get('headers'))
            if path.startswith('/objects/'):
                cap = runtime.transport.capabilities.get(path.split('/')[-1])
                if not cap or cap[0] != self.command or cap[2] <= time.time():
                    return self.send(403, '{}')
                if self.command == 'GET':
                    try:
                        item = runtime.s3.get_object(**cap[1])
                        return self.send(200, item['Body'].read(), item.get('ContentType', 'application/octet-stream'))
                    except runtime.s3.exceptions.NoSuchKey:
                        return self.send(404, '{}')
                # Parse multipart with the standard email parser (no deprecated cgi).
                from email.parser import BytesParser
                from email.policy import default
                raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                message = BytesParser(policy=default).parsebytes(
                    ('Content-Type: ' + self.headers.get('Content-Type', '') + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + raw)
                fields, data = {}, None
                for part in message.iter_parts():
                    name = part.get_param('name', header='content-disposition')
                    if name == 'file': data = part.get_payload(decode=True)
                    else: fields[name] = part.get_payload(decode=True).decode()
                if fields != cap[3] or data is None or not 1 <= len(data) <= 52428800:
                    return self.send(403, '{}')
                runtime.s3.put_object(Bucket=cap[1]['Bucket'], Key=cap[1]['Key'],
                    Body=data, ContentType=fields.get('Content-Type', 'application/octet-stream'))
                return self.send(204)
            if self.command != 'GET':
                return self.send(404, '{}')
            if path == '/health':
                return self.send(200, '{"status":"local-test"}')
            # Only local responses override API config; tracked source is untouched.
            if path.endswith('/auth-config.json'):
                return self.send(200, json.dumps({'apiBaseUrl': runtime.base + '/api/auth', 'ownerDiscordUserId': ''}))
            if path.endswith('/authority-config.json'):
                return self.send(200, json.dumps({'apiBaseUrl': runtime.base + '/api/authority', 'realtimeUrl': ''}))
            if path.startswith('/Game/'):
                candidate = WWWROOT / (path[6:] or 'index.html')
                root = WWWROOT
            elif path.startswith('/Launcher/'):
                candidate = WWWROOT / 'Launcher' / (path[10:] or 'index.html')
                root = WWWROOT
            else:
                root = ROOT / 'site/relic-home'
                candidate = root / path.lstrip('/')
                if path.endswith('/'): candidate /= 'index.html'
            candidate = candidate.resolve()
            if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
                return self.send(404, '{}')
            return self.send(200, candidate.read_bytes(), mimetypes.guess_type(candidate)[0] or 'application/octet-stream')

        def do_GET(self): self.handle_request()
        def do_POST(self): self.handle_request()
        def do_OPTIONS(self): self.handle_request()
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    require_test_environment()
    marker = RUNTIME / 'build.json'
    if not marker.is_file() or json.loads(marker.read_text()) != {'environment': 'test', 'configuration': 'Debug'} or not (WWWROOT / 'index.html').is_file():
        raise RuntimeError('Only the isolated Debug test build is accepted; run build_local.py')
    runtime = Runtime('http://127.0.0.1:' + str(args.port))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(runtime))
    # No HTTP login or session-minting endpoint. Fixture state travels via private disk.
    for persona, state in runtime.sessions.items():
        write_private_json(RUNTIME / '.auth' / (persona + '.json'), state)
    print('Local test harness ready on loopback; credentials are not logged', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        server.server_close()
        runtime.close()
        for path in (RUNTIME / '.auth').glob('*.json'): path.unlink()


if __name__ == '__main__': main()
