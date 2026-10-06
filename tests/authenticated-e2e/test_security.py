import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import threading
import http.client
from http.server import ThreadingHTTPServer
import pytest
from local_harness import Runtime, require_test_environment, make_handler, ROOT

TEST_ENV = {'SHAELVIEN_TEST_AUTH': '1', 'SHAELVIEN_ENVIRONMENT': 'test',
            'DOTNET_ENVIRONMENT': 'Development', 'NODE_ENV': 'test'}


@pytest.fixture
def runtime(monkeypatch):
    for key, value in TEST_ENV.items(): monkeypatch.setenv(key, value)
    instance = Runtime()
    yield instance
    instance.close()


@pytest.mark.parametrize('override', [
    {'SHAELVIEN_TEST_AUTH': '0'}, {'SHAELVIEN_ENVIRONMENT': 'production'},
    {'DOTNET_ENVIRONMENT': 'Production'}, {'NODE_ENV': 'production'},
    {'SHAELVIEN_ENVIRONMENT': ''}, {'DOTNET_ENVIRONMENT': ''}, {'NODE_ENV': ''},
])
def test_independent_environment_gates(override):
    with pytest.raises(RuntimeError): require_test_environment({**TEST_ENV, **override})


def test_flag_alone_cannot_activate():
    with pytest.raises(RuntimeError): require_test_environment({'SHAELVIEN_TEST_AUTH': '1'})


def test_production_build_and_nonlocal_hosts_rejected():
    for options in ({'host': '0.0.0.0'}, {'host': 'relicgamemaster.com'}, {'build_configuration': 'Release'}):
        with pytest.raises(RuntimeError): require_test_environment(TEST_ENV, **options)


@pytest.mark.parametrize('service,path', [
    ('auth', '/me'), ('auth', '/storage/list'), ('auth', '/storage/download?key=account/profile.json'),
    ('authority', '/authority/me'), ('authority', '/world/source?worldId=e2e-shared'),
    ('authority', '/world/regions?worldId=e2e-shared'), ('authority', '/authority/owner/dashboard'),
])
def test_actual_handlers_reject_missing_and_forged_tokens(runtime, service, path):
    for token in ('', 'forged-session'):
        assert runtime.dispatch(service, 'GET', path, token)['statusCode'] == 401


def test_expiry_and_revocation_checked_by_both_handlers(runtime):
    token = runtime.sessions['user']['token']
    key = {'pk': 'session#' + hashlib.sha256(token.encode()).hexdigest()}
    item = runtime.auth.ddb.get_item(Key=key)['Item']
    item['expiresAt'] = int(time.time()) - 1
    runtime.auth.ddb.put_item(Item=item)
    for service, path in [('auth', '/me'), ('authority', '/authority/me')]:
        assert runtime.dispatch(service, 'GET', path, token)['statusCode'] == 401
    runtime.auth.ddb.delete_item(Key=key)
    assert runtime.dispatch('auth', 'GET', '/me', token)['statusCode'] == 401


def test_personas_go_through_real_permission_and_owner_checks(runtime):
    user, gm = [runtime.sessions[name]['token'] for name in ('user', 'gm')]
    profile = runtime.dispatch('authority', 'GET', '/authority/me', user)
    assert profile['statusCode'] == 200
    profile = json.loads(profile['body'])
    assert profile['platformOwner'] is False
    assert 'access.gamemaster' not in profile['entitlements']
    assert 'access.developer' not in profile['entitlements']
    assert runtime.dispatch('authority', 'GET', '/authority/owner/dashboard', user)['statusCode'] == 403
    mutation = {'worldId': 'e2e-shared', 'state': {'name': 'fixture state'}}
    assert runtime.dispatch('authority', 'POST', '/world/source', user, mutation)['statusCode'] == 403
    assert runtime.dispatch('authority', 'POST', '/world/source', gm, mutation)['statusCode'] == 200
    assert runtime.dispatch('authority', 'GET', '/world/source?worldId=e2e-unrelated', gm)['statusCode'] == 403
    assert runtime.dispatch('authority', 'POST', '/world/source', gm,
        {**mutation, 'worldId': runtime.authority.GEONAPH_WORLD_ID})['statusCode'] == 403
    # Session/role hints supplied by clients never manufacture platform authority.
    assert runtime.dispatch('authority', 'POST', '/world/source', user,
        {**mutation, 'role': 'owner', 'platformOwner': True})['statusCode'] == 403


def test_owner_profile_route_uses_global_owner_not_deed_local(runtime):
    # Regression for a live source defect: deed-request branch previously shadowed
    # the module owner ID throughout handler(), crashing /authority/me.
    assert runtime.dispatch('authority', 'GET', '/authority/me', runtime.sessions['gm']['token'])['statusCode'] == 200


def test_handoff_remains_real_single_use_validation(runtime):
    token = runtime.sessions['gm']['token']
    runtime.auth.ddb.put_item(Item={'pk': 'handoff#fixture', 'sessionToken': token,
        'provider': 'discord', 'sessionExpiresAt': int(time.time()) + 60, 'expiresAt': int(time.time()) + 60})
    assert runtime.dispatch('auth', 'GET', '/auth/session?handoff=fixture')['statusCode'] == 200
    assert runtime.dispatch('auth', 'GET', '/auth/session?handoff=fixture')['statusCode'] == 400


def test_generated_state_is_ignored_and_not_tracked():
    for name in ('.e2e-runtime/.auth/gm.json', '.e2e-runtime/build.json', 'playwright/.auth/storageState.json'):
        result = subprocess.run(['git', 'check-ignore', name], cwd=ROOT, capture_output=True)
        assert result.returncode == 0
    tracked = subprocess.check_output(['git', 'ls-files', '.e2e-runtime', '*/.auth/*'], cwd=ROOT)
    assert tracked == b''


def test_fixture_code_is_not_in_production_publish_tree():
    webroot = ROOT / 'apps/rist-world/wwwroot'
    assert not (webroot / 'local_harness.py').exists()
    assert not (webroot / 'auth-state.cjs').exists()
    production_auth = (ROOT / 'infra/aws/rist-discord-storage.yml').read_text()
    assert '/test-login' not in production_auth
    assert '/bypass' not in production_auth
    assert 'SHAELVIEN_TEST_AUTH' not in production_auth
    assert 'SHAELVIEN_TEST_AUTH' not in (ROOT / 'apps/rist-world/DiscordAuthClient.cs').read_text()
    assert 'SHAELVIEN_TEST_AUTH' not in (ROOT / 'infra/aws/rist-platform-authority/app.py').read_text()


def test_disabled_configuration_leaves_no_provider(monkeypatch):
    for key in TEST_ENV: monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError): Runtime()


def test_http_host_origin_and_no_magic_session(runtime):
    server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(runtime))
    runtime.base = 'http://127.0.0.1:' + str(server.server_port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(path, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
        connection.request('GET', path, headers=headers or {})
        response = connection.getresponse()
        response.read()
        connection.close()
        return response.status
    try:
        assert request('/health', {'Host': 'attacker.example'}) == 403
        assert request('/health', {'Origin': 'https://attacker.example'}) == 403
        assert request('/api/auth/me?test-auth=1&bypass=1', {'Cookie': 'rist_session=magic'}) == 401
        assert request('/objects/forged') == 403
        for path in ('/test-login', '/bypass', '/api/auth/test-login', '/api/auth/bypass'):
            assert request(path) != 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize('environment', [
    {'SHAELVIEN_TEST_AUTH': '1'},
    {**TEST_ENV, 'DOTNET_ENVIRONMENT': 'Production'},
    {**TEST_ENV, 'NODE_ENV': 'production'},
])
def test_executable_fails_closed_before_server_start(environment):
    env = {k: v for k, v in os.environ.items() if k not in TEST_ENV}
    result = subprocess.run(['python3', str(Path(__file__).with_name('local_harness.py'))],
        env={**env, **environment}, capture_output=True, timeout=10)
    assert result.returncode != 0
    assert b'Local test harness ready' not in result.stdout
