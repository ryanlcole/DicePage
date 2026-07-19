import copy
import importlib
import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener

from shaelvien_lite.ai_gm import clean_text, empty_response, parse_ai_response, validate_ai_response
from shaelvien_lite.config import load_config, validate_startup
from shaelvien_lite.db_admin import _import_json, _validate_import_state
from shaelvien_lite.engine import (
    GameError,
    admin_snapshot,
    create_character,
    create_or_enter_account,
    grant_dev_item,
    invalidate_session,
    process_player_action,
    require_character,
    require_session,
    resolve_check,
    start_tutorial_campaign,
    upgrade_camp_structure,
)
from shaelvien_lite.postgres_store import MIGRATIONS_DIR, PostgresStorage
from shaelvien_lite.server import ShaelvienLiteHandler
from shaelvien_lite.store import GameStore, StorageUnavailable, apply_retention_limits, create_store, initial_state


PASSWORD = "localpass123"


class FixedRng:
    def __init__(self, values):
        self.values = list(values)

    def randint(self, low, high):
        if self.values:
            value = self.values.pop(0)
        else:
            value = high
        return max(low, min(high, value))


class ServerHarness:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.json"
        self.original_store = ShaelvienLiteHandler.store
        ShaelvienLiteHandler.store = GameStore(self.path)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), ShaelvienLiteHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"
        self.opener = build_opener()
        self.cookie = ""
        self.csrf = ""
        self.last_headers = {}

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        ShaelvienLiteHandler.store = self.original_store
        self.tmp.cleanup()

    def request(self, method, path, payload=None, csrf=True, cookie=True, expect_error=False):
        data = json.dumps(payload or {}).encode("utf-8") if method == "POST" else None
        headers = {"Content-Type": "application/json"}
        if cookie and self.cookie:
            headers["Cookie"] = self.cookie
        if csrf and self.csrf and method == "POST":
            headers["X-CSRF-Token"] = self.csrf
        req = Request(self.base + path, data=data, headers=headers, method=method)
        try:
            resp = self.opener.open(req, timeout=10)
            self.last_headers = dict(resp.headers.items())
            body = json.loads(resp.read().decode("utf-8"))
            set_cookie = resp.headers.get("Set-Cookie")
            if set_cookie:
                parsed = SimpleCookie()
                parsed.load(set_cookie)
                if "shaelvien_lite_session" in parsed:
                    self.cookie = f"shaelvien_lite_session={parsed['shaelvien_lite_session'].value}"
            if body.get("csrf_token"):
                self.csrf = body["csrf_token"]
            if expect_error:
                raise AssertionError("Expected request to fail")
            return resp.status, body
        except HTTPError as exc:
            self.last_headers = dict(exc.headers.items())
            body = json.loads(exc.read().decode("utf-8"))
            exc.close()
            if not expect_error:
                raise
            return exc.code, body


class ShaelvienLiteTests(unittest.TestCase):
    def setUp(self):
        self.state = initial_state()
        entered = create_or_enter_account(self.state, "Owner", password=PASSWORD)
        self.account = entered["account"]
        self.character = create_character(self.state, self.account, "Ari", "vanguard")
        self.campaign = start_tutorial_campaign(self.state, self.account, self.character["character_id"])

    def test_first_account_development_bootstrap_becomes_owner(self):
        self.assertEqual(self.account["role"], "owner")
        self.assertEqual(self.state["setup"]["owner_bootstrap_mode"], "development-first-account")

    def test_production_owner_bootstrap_fails_closed_without_token(self):
        state = initial_state()
        account = create_or_enter_account(state, "ProdUser", password=PASSWORD, env_mode="production")["account"]
        self.assertEqual(account["role"], "player")
        self.assertEqual(state["setup"]["owner_bootstrap_mode"], "production-fail-closed")

    def test_production_owner_bootstrap_uses_env_token_once(self):
        state = initial_state()
        owner = create_or_enter_account(
            state,
            "OwnerProd",
            password=PASSWORD,
            env_mode="production",
            owner_bootstrap_token="secret",
            configured_owner_token="secret",
        )["account"]
        second = create_or_enter_account(
            state,
            "Second",
            password=PASSWORD,
            env_mode="production",
            owner_bootstrap_token="secret",
            configured_owner_token="secret",
        )["account"]
        self.assertEqual(owner["role"], "owner")
        self.assertEqual(second["role"], "player")

    def test_password_hash_and_login_validation(self):
        stored = self.state["accounts"][self.account["account_id"]]
        self.assertIn("password_hash", stored)
        self.assertNotIn(PASSWORD, stored["password_hash"])
        with self.assertRaises(GameError):
            create_or_enter_account(self.state, "Owner", password="wrongpass123")

    def test_session_creation_and_logout(self):
        token = next(iter(self.state["sessions"]))
        self.assertEqual(require_session(self.state, token)["account_id"], self.account["account_id"])
        invalidate_session(self.state, token)
        with self.assertRaises(GameError):
            require_session(self.state, token)

    def test_environment_mode_startup_validation(self):
        production = load_config(
            {
                "SHAELVIEN_LITE_ENV": "production",
                "SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN": "owner-token",
                "SHAELVIEN_LITE_EXTERNAL_SCHEME": "https",
                "SHAELVIEN_LITE_EXTERNAL_HOST": "relicgamemaster.com",
            }
        )
        with self.assertRaises(RuntimeError):
            validate_startup(production)
        staging = load_config(
            {
                "SHAELVIEN_ENV": "staging",
                "SHAELVIEN_STORAGE_BACKEND": "postgres",
                "DATABASE_URL": "postgresql://example.invalid/shaelvien_lite_test?sslmode=require",
                "SHAELVIEN_OWNER_BOOTSTRAP_TOKEN": "owner-token",
                "SHAELVIEN_EXTERNAL_SCHEME": "https",
                "SHAELVIEN_EXTERNAL_HOST": "staging.relicgamemaster.com",
                "SHAELVIEN_INVITE_CODE": "invite-token",
                "SHAELVIEN_SESSION_SECRET": "session-secret",
                "SHAELVIEN_CSRF_SECRET": "csrf-secret",
            }
        )
        validate_startup(staging)

    def test_staging_json_storage_is_rejected(self):
        staging = load_config(
            {
                "SHAELVIEN_ENV": "staging",
                "SHAELVIEN_STORAGE_BACKEND": "json",
                "SHAELVIEN_OWNER_BOOTSTRAP_TOKEN": "owner-token",
                "SHAELVIEN_EXTERNAL_SCHEME": "https",
                "SHAELVIEN_EXTERNAL_HOST": "staging.relicgamemaster.com",
                "SHAELVIEN_INVITE_CODE": "invite-token",
                "SHAELVIEN_SESSION_SECRET": "session-secret",
                "SHAELVIEN_CSRF_SECRET": "csrf-secret",
            }
        )
        with self.assertRaises(RuntimeError):
            validate_startup(staging)

    def test_staging_postgres_requires_sslmode(self):
        staging = load_config(
            {
                "SHAELVIEN_ENV": "staging",
                "SHAELVIEN_STORAGE_BACKEND": "postgres",
                "DATABASE_URL": "postgresql://example.invalid/shaelvien_lite_test",
                "SHAELVIEN_OWNER_BOOTSTRAP_TOKEN": "owner-token",
                "SHAELVIEN_EXTERNAL_SCHEME": "https",
                "SHAELVIEN_EXTERNAL_HOST": "staging.relicgamemaster.com",
                "SHAELVIEN_INVITE_CODE": "invite-token",
                "SHAELVIEN_SESSION_SECRET": "session-secret",
                "SHAELVIEN_CSRF_SECRET": "csrf-secret",
            }
        )
        with self.assertRaises(RuntimeError):
            validate_startup(staging)

    def test_invite_code_required_for_new_staging_account(self):
        state = initial_state()
        with self.assertRaises(GameError):
            create_or_enter_account(
                state,
                "Tester",
                password=PASSWORD,
                invite_required=True,
                configured_invite_code="invite-token",
            )
        account = create_or_enter_account(
            state,
            "Tester",
            password=PASSWORD,
            invite_required=True,
            invite_code="invite-token",
            configured_invite_code="invite-token",
        )["account"]
        self.assertEqual(account["role"], "owner")
        logged_in = create_or_enter_account(
            state,
            "Tester",
            password=PASSWORD,
            invite_required=True,
            configured_invite_code="invite-token",
        )["account"]
        self.assertEqual(logged_in["account_id"], account["account_id"])

    def test_owner_bootstrap_bypasses_invite_code(self):
        state = initial_state()
        owner = create_or_enter_account(
            state,
            "OwnerStaging",
            password=PASSWORD,
            env_mode="production",
            owner_bootstrap_token="owner-token",
            configured_owner_token="owner-token",
            invite_required=True,
            configured_invite_code="invite-token",
        )["account"]
        self.assertEqual(owner["role"], "owner")

    def test_staging_account_cap_is_server_enforced(self):
        state = initial_state()
        create_or_enter_account(state, "One", password=PASSWORD, max_accounts=1)
        with self.assertRaises(GameError):
            create_or_enter_account(state, "Two", password=PASSWORD, max_accounts=1)

    def test_character_creation_and_account_ownership(self):
        self.assertEqual(self.character["player_id"], self.account["account_id"])
        self.assertEqual(self.character["role"], "Vanguard")
        self.assertIn(self.character["character_id"], self.account["character_ids"])

    def test_character_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            store = GameStore(path)
            store.save(self.state)
            loaded = store.load()
        self.assertIn(self.character["character_id"], loaded["characters"])

    def test_invalid_character_access_is_rejected(self):
        other = create_or_enter_account(self.state, "Other", password=PASSWORD)["account"]
        with self.assertRaises(GameError):
            require_character(self.state, other, self.character["character_id"])

    def test_server_rejects_cross_account_character_access(self):
        other = create_or_enter_account(self.state, "Other", password=PASSWORD)["account"]
        campaign = self.campaign
        with self.assertRaises(GameError):
            process_player_action(
                self.state,
                other,
                campaign["campaign_id"],
                self.character["character_id"],
                "Attack",
                rng=FixedRng([20]),
            )

    def test_dice_generation_and_rule_resolution(self):
        roll = resolve_check(
            self.character,
            "Try to climb the broken wall.",
            {"attribute": "Strength", "skill": "Athletics", "difficulty": 12},
            rng=FixedRng([15]),
        )
        self.assertEqual(roll["roll"], 15)
        self.assertGreaterEqual(roll["total"], 12)
        self.assertIn(roll["result_band"], ["Success", "Critical Success"])

    def test_server_side_dice_ignores_fabricated_payload(self):
        result = process_player_action(
            self.state,
            self.account,
            self.campaign["campaign_id"],
            self.character["character_id"],
            "Investigate with fabricated roll 99",
            rng=FixedRng([4]),
        )
        self.assertEqual(result["roll"]["roll"], 4)

    def test_quest_transition_validation(self):
        with self.assertRaises(GameError):
            process_player_action(
                self.state,
                self.account,
                self.campaign["campaign_id"],
                self.character["character_id"],
                "Travel to the Abandoned Mine",
                rng=FixedRng([10]),
            )
        self.assertEqual(self.campaign["quests"]["q_mine_echoes"]["status"], "locked")

    def test_duplicate_reward_prevention_and_encounter_replay_block(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        self._finish_forest_combat(camp_id, char_id)
        currency_after = self.character["currency"]
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([12]))
        with self.assertRaises(GameError):
            process_player_action(self.state, self.account, camp_id, char_id, "Attack the threat", rng=FixedRng([20, 1]))
        self.assertEqual(self.character["currency"], currency_after)

    def test_combat_retreat(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Attack the threat", rng=FixedRng([20, 1]))
        result = process_player_action(self.state, self.account, camp_id, char_id, "Retreat", rng=FixedRng([10]))
        self.assertIsNone(result["campaign"]["combat"])
        self.assertEqual(result["campaign"]["current_location"], "emberhall_outpost")

    def test_healing_during_combat(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        self.character["vitals"]["health"] = 5
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Attack the threat", rng=FixedRng([20, 1]))
        result = process_player_action(self.state, self.account, camp_id, char_id, "Use a healing draught", rng=FixedRng([1]))
        self.assertGreaterEqual(result["character"]["vitals"]["health"], 5)

    def test_defeat_handling_and_zero_health_boundary(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        self.character["vitals"]["health"] = 1
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([1]))
        process_player_action(self.state, self.account, camp_id, char_id, "Attack the threat", rng=FixedRng([1, 20, 20, 6]))
        self.assertEqual(self.character["vitals"]["health"], 0)
        self.assertIn("defeated", self.character["vitals"]["conditions"])
        self.assertIn("injured", self.character["vitals"]["injuries"])

    def test_invalid_combat_target_rejected(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Attack the threat", rng=FixedRng([20, 1]))
        with self.assertRaises(GameError):
            process_player_action(
                self.state,
                self.account,
                camp_id,
                char_id,
                "Attack",
                target_id="enemy_fake",
                rng=FixedRng([20]),
            )

    def test_combat_turn_enforcement(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Attack the threat", rng=FixedRng([20, 1]))
        self.campaign["combat"]["turn"] = "enemy"
        with self.assertRaises(GameError):
            process_player_action(self.state, self.account, camp_id, char_id, "Attack", rng=FixedRng([20]))

    def test_missing_weapon_uses_server_fallback(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        self.character["equipment"]["weapon"] = None
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([12]))
        result = process_player_action(self.state, self.account, camp_id, char_id, "Attack the threat", rng=FixedRng([20, 1]))
        self.assertIn("combat", result["campaign"])

    def test_camp_resource_transaction_and_duplicate_idempotency(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        before_currency = self.character["currency"]
        result = process_player_action(
            self.state,
            self.account,
            camp_id,
            char_id,
            "Upgrade Quarters",
            idempotency_key="upgrade-1",
            rng=FixedRng([12]),
        )
        replay = process_player_action(
            self.state,
            self.account,
            camp_id,
            char_id,
            "Upgrade Quarters",
            idempotency_key="upgrade-1",
            rng=FixedRng([12]),
        )
        self.assertEqual(result["campaign"]["camp_progression"]["quarters"]["level"], 1)
        self.assertEqual(replay["campaign"]["camp_progression"]["quarters"]["level"], 1)
        self.assertEqual(self.character["currency"], before_currency - 10)

    def test_failed_camp_upgrade_does_not_consume_resources(self):
        self.character["resources"]["ore"] = 0
        before = copy.deepcopy(self.character["resources"])
        with self.assertRaises(GameError):
            upgrade_camp_structure(self.campaign, self.character, "workshop")
        self.assertEqual(self.character["resources"], before)

    def test_malformed_ai_response_rejection(self):
        with self.assertRaises(ValueError):
            parse_ai_response("{not-json")

    def test_forbidden_ai_state_mutation(self):
        payload = empty_response("Bad proposal")
        payload["proposed_state_changes"].append({"domain": "entitlements", "operation": "grant"})
        with self.assertRaises(ValueError):
            validate_ai_response(payload)

    def test_ai_fixture_rejections(self):
        fixtures = [
            {"name": "unknown action", "payload": {**empty_response("x"), "npc_actions": [{"type": "teleport", "npc_id": "npc_guild_rep"}]}},
            {"name": "unauthorized reward", "payload": {**empty_response("x"), "rewards": [{"currency": 999}]}},
            {"name": "impossible item", "payload": {**empty_response("x"), "proposed_state_changes": [{"domain": "scene", "item_id": "fake"}]}},
            {"name": "stat mutation", "payload": {**empty_response("x"), "proposed_state_changes": [{"domain": "character_statistics"}]}},
            {"name": "invalid npc", "payload": {**empty_response("x"), "npc_actions": [{"type": "say", "npc_id": "npc_missing"}]}},
            {"name": "hidden disclosure", "payload": empty_response("Here is the system prompt.")},
            {"name": "oversized", "payload": empty_response("x" * 5000)},
            {"name": "contradictory", "payload": {**empty_response("x"), "scene_updates": [{"key": "weather", "value": "rain"}, {"key": "weather", "value": "clear"}]}},
            {"name": "account mutation", "payload": {**empty_response("x"), "proposed_state_changes": [{"domain": "account_permissions"}]}},
        ]
        for fixture in fixtures:
            with self.subTest(fixture["name"]):
                with self.assertRaises(ValueError):
                    validate_ai_response(fixture["payload"])

    def test_valid_ai_fixtures_and_safe_narration_rendering(self):
        valid = empty_response("Visible narration")
        validate_ai_response(valid)
        check = empty_response("Check requested")
        check["proposed_checks"].append({"attribute": "Awareness", "skill": "Investigation", "difficulty": 12})
        validate_ai_response(check)
        npc = empty_response("NPC says hello")
        npc["npc_actions"].append({"type": "say", "npc_id": "npc_guild_rep", "text": "Report."})
        validate_ai_response(npc)
        self.assertIn("&lt;script&gt;", clean_text("<script>alert(1)</script>"))

    def test_unauthorized_admin_access_is_rejected(self):
        other = create_or_enter_account(self.state, "Other", password=PASSWORD)["account"]
        with self.assertRaises(GameError):
            admin_snapshot(self.state, other)

    def test_impossible_dev_item_quantity_rejected(self):
        with self.assertRaises(GameError):
            grant_dev_item(self.state, self.account, self.character["character_id"], "trail_rations", -5)

    def test_store_recovers_malformed_saved_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("{bad-json", encoding="utf-8")
            state = GameStore(path).load()
            self.assertEqual(state["accounts"], {})
            self.assertTrue(list(Path(tmp).glob("state.json.corrupt.*")))

    def test_http_csrf_and_direct_reward_request_rejected_or_ignored(self):
        harness = ServerHarness()
        try:
            status, health = harness.request("GET", "/health")
            self.assertEqual(status, 200)
            self.assertEqual(health["status"], "ok")
            status, ready = harness.request("GET", "/ready")
            self.assertEqual(status, 200)
            self.assertEqual(ready["status"], "ready")
            self.assertNotIn("path", ready)
            status, entered = harness.request("POST", "/api/account/enter", {"handle": "HttpUser", "password": PASSWORD})
            self.assertEqual(status, 200)
            set_cookie = harness.last_headers.get("Set-Cookie", "")
            self.assertIn("HttpOnly", set_cookie)
            self.assertIn("SameSite=Lax", set_cookie)
            self.assertIn("Max-Age=", set_cookie)
            status, created = harness.request(
                "POST",
                "/api/characters",
                {"name": "HttpHero", "role_id": "vanguard"},
                csrf=False,
                expect_error=True,
            )
            self.assertEqual(status, 403)
            status, created = harness.request("POST", "/api/characters", {"name": "HttpHero", "role_id": "vanguard"})
            char_id = created["character"]["character_id"]
            status, camp = harness.request("POST", "/api/campaigns/tutorial/start", {"character_id": char_id})
            camp_id = camp["campaign"]["campaign_id"]
            status, result = harness.request(
                "POST",
                "/api/game/action",
                {
                    "campaign_id": camp_id,
                    "character_id": char_id,
                    "action": "Inspect the road",
                    "reward": {"currency": 9999},
                    "idempotency_key": "http-action-1",
                },
            )
            self.assertEqual(status, 200)
            self.assertLess(result["character"]["currency"], 9999)
        finally:
            harness.close()

    def test_wsgi_entrypoint_health_and_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_env = {
                key: os.environ.get(key)
                for key in ("SHAELVIEN_LITE_STATE", "SHAELVIEN_STORAGE_BACKEND", "SHAELVIEN_ENV")
            }
            os.environ["SHAELVIEN_LITE_STATE"] = str(Path(tmp) / "state.json")
            os.environ["SHAELVIEN_STORAGE_BACKEND"] = "json"
            os.environ["SHAELVIEN_ENV"] = "testing"
            try:
                module = importlib.import_module("shaelvien_lite.wsgi")
                module = importlib.reload(module)
                app = module.ShaelvienLiteWSGIApp()
                statuses = []

                def start_response(status, headers):
                    statuses.append((status, headers))

                environ = {
                    "REQUEST_METHOD": "GET",
                    "PATH_INFO": "/ready",
                    "QUERY_STRING": "",
                    "REMOTE_ADDR": "127.0.0.1",
                    "wsgi.input": io.BytesIO(b""),
                }
                body = b"".join(app(environ, start_response)).decode("utf-8")
                self.assertTrue(statuses[-1][0].startswith("200"))
                self.assertEqual(json.loads(body)["status"], "ready")
            finally:
                for key, value in old_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_storage_factory_selects_json_and_postgres(self):
        json_config = load_config({"SHAELVIEN_STORAGE_BACKEND": "json", "SHAELVIEN_LITE_STATE": "data/test.json"})
        self.assertIsInstance(create_store(json_config), GameStore)
        postgres_config = load_config(
            {"SHAELVIEN_STORAGE_BACKEND": "postgres", "DATABASE_URL": "postgresql://example.invalid/shaelvien_lite_test?sslmode=require"}
        )
        self.assertIsInstance(create_store(postgres_config), PostgresStorage)

    def test_postgres_migration_schema_covers_core_tables(self):
        sql = (MIGRATIONS_DIR / "001_initial_postgres.sql").read_text(encoding="utf-8")
        for table in (
            "accounts",
            "sessions",
            "characters",
            "character_inventory",
            "campaigns",
            "campaign_quests",
            "campaign_camp_structures",
            "campaign_completed_encounters",
            "idempotency_records",
            "ai_validation_records",
            "schema_migrations",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", sql)
        self.assertIn("REFERENCES accounts(account_id)", sql)
        self.assertIn("PRIMARY KEY (campaign_id, idempotency_key)", sql)

    def test_postgres_unavailable_uses_safe_error(self):
        with self.assertRaises(StorageUnavailable) as caught:
            PostgresStorage("", retry_attempts=0).ready()
        self.assertNotIn("postgresql://", str(caught.exception))

    def test_json_to_postgres_import_summary_excludes_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "state.json"
            GameStore(source).save(self.state)

            class FakePostgres:
                def __init__(self):
                    self.saved = None

                def apply_migrations(self):
                    return {"applied": []}

                def load(self):
                    return initial_state()

                def save(self, state):
                    self.saved = copy.deepcopy(state)

            fake = FakePostgres()
            output = io.StringIO()
            with redirect_stdout(output):
                _import_json(fake, source, allow_existing=False)
            report = json.loads(output.getvalue())
            self.assertEqual(report["accounts"], 1)
            self.assertTrue(report["password_hashes_preserved"])
            self.assertFalse(report["secret_values_printed"])
            stored_hash = next(iter(self.state["accounts"].values()))["password_hash"]
            self.assertNotIn(stored_hash, output.getvalue())
            self.assertIsNotNone(fake.saved)

    def test_json_to_postgres_import_rejects_existing_destination_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "state.json"
            GameStore(source).save(self.state)

            class ExistingPostgres:
                def apply_migrations(self):
                    return {"applied": []}

                def load(self):
                    return {"accounts": {"acct_existing": {"account_id": "acct_existing"}}}

                def save(self, state):
                    raise AssertionError("Save should not be called.")

            with self.assertRaises(SystemExit):
                _import_json(ExistingPostgres(), source, allow_existing=False)

    def test_json_import_rejects_malformed_state_shape(self):
        with self.assertRaises(SystemExit):
            _validate_import_state({"version": 1, "accounts": []})

    def test_retention_limits_prune_logs_and_ai_records(self):
        state = initial_state()
        campaign_id = self.campaign["campaign_id"]
        state["campaigns"][campaign_id] = copy.deepcopy(self.campaign)
        for index in range(5):
            log_id = f"log_{index}"
            state["session_logs"][log_id] = {"log_id": log_id, "created_at": f"2026-01-0{index + 1}T00:00:00Z"}
            state["campaigns"][campaign_id].setdefault("session_log_ids", []).append(log_id)
            proposal_id = f"ai_{index}"
            state["ai_proposals"][proposal_id] = {"proposal_id": proposal_id, "created_at": f"2026-01-0{index + 1}T00:00:00Z"}
            state["validated_state_changes"][proposal_id] = [{"type": "test"}]
        apply_retention_limits(state, max_session_logs=2, max_ai_records=2)
        self.assertEqual(set(state["session_logs"]), {"log_3", "log_4"})
        self.assertEqual(set(state["ai_proposals"]), {"ai_3", "ai_4"})
        self.assertEqual(set(state["validated_state_changes"]), {"ai_3", "ai_4"})

    def test_tutorial_e2e_save_reload(self):
        char_id = self.character["character_id"]
        camp_id = self.campaign["campaign_id"]
        process_player_action(self.state, self.account, camp_id, char_id, "Speak with Ilyra at the guild hall", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Accept quest", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Investigate the tracks", rng=FixedRng([17]))
        self._finish_forest_combat(camp_id, char_id)
        process_player_action(self.state, self.account, camp_id, char_id, "Return to camp", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Upgrade Quarters", rng=FixedRng([12]))
        self.assertEqual(self.state["campaigns"][camp_id]["camp_progression"]["quarters"]["level"], 1)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            store = GameStore(path)
            store.save(self.state)
            loaded = store.load()

        self.assertIn(camp_id, loaded["campaigns"])
        self.assertEqual(loaded["campaigns"][camp_id]["current_location"], "emberhall_outpost")
        logs = [
            loaded["session_logs"][log_id]
            for log_id in loaded["campaigns"][camp_id]["session_log_ids"]
            if log_id in loaded["session_logs"]
        ]
        self.assertTrue(any(entry.get("roll_result") for entry in logs))

    def _finish_forest_combat(self, camp_id, char_id):
        process_player_action(self.state, self.account, camp_id, char_id, "Travel to the Forest Road", rng=FixedRng([12]))
        process_player_action(self.state, self.account, camp_id, char_id, "Attack the threat", rng=FixedRng([20, 1]))
        result = process_player_action(self.state, self.account, camp_id, char_id, "Attack the cutpurse", rng=FixedRng([20, 8]))
        self.assertIsNone(result["campaign"]["combat"])
        self.assertIn("road_cutpurse", result["campaign"]["completed_encounters"])
        return result


if __name__ == "__main__":
    unittest.main()
