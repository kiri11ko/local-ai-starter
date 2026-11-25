"""Strata engine plumbing: profiles, plan checks, launch command, installed matching, OpenCode config.

No network and no real `strata` calls: the control binary is stubbed.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import local_ai_starter as app


class StrataProfileTests(unittest.TestCase):
    def test_strata_profiles_are_registered(self):
        strata = [p for p in app._MODELS if p.engine == "strata"]
        self.assertEqual(len(strata), 5)
        self.assertEqual(len({p.key for p in strata}), 5)
        for profile in strata:
            self.assertTrue(profile.family, profile.key)
            self.assertTrue(profile.file, profile.key)
            self.assertTrue(profile.min_ram_gb >= 16, profile.key)

    def test_api_model(self):
        strata = next(p for p in app._MODELS if p.engine == "strata")
        gguf = next(p for p in app._MODELS if p.engine == "gguf")
        self.assertEqual(app.api_model(strata), "strata")
        self.assertEqual(app.api_model(gguf), gguf.key)

    def test_env_stays_inside_engines_dir(self):
        env = app.strata_env()
        self.assertEqual(env["STRATA_DATA_DIR"], str(app.STRATA_DIR))
        self.assertEqual(env["STRATA_BIN_DIR"], str(app.STRATA_DIR / "bin"))

    def test_launch_command_flags(self):
        profile = app.PROFILES["inkling-2-mini-sq10"]
        with patch.object(app, "strata_binary", return_value=app.STRATA_DIR / "bin" / "strata"):
            command = app.strata_launch_command(profile, 8123, 32768)
        joined = " ".join(command)
        self.assertIn("--yes --no-tui", joined)
        self.assertIn("--api-key-env LOCAL_AI_STARTER_STRATA_KEY", joined)
        self.assertIn("--port 8123", joined)
        self.assertIn("--context 32768", joined)
        self.assertIn(str(app.STRATA_DIR / "data"), joined)

    def test_opencode_config_uses_strata_model_and_key(self):
        profile = app.PROFILES["inkling-2-mini-sq10"]
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(app, "ROOT", Path(tmp)), patch.object(app, "OPENCODE_CONFIG", Path(tmp) / "opencode.json"):
                app.write_opencode_config(profile, 8080, 32768, "secret-key")
                config = json.loads((Path(tmp) / "opencode.json").read_text(encoding="utf-8"))
        options = config["provider"]["local-ai-starter"]["options"]
        self.assertEqual(config["model"], "local-ai-starter/strata")
        self.assertEqual(options["apiKey"], "secret-key")
        gguf = next(p for p in app._MODELS if p.engine == "gguf")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(app, "ROOT", Path(tmp)), patch.object(app, "OPENCODE_CONFIG", Path(tmp) / "opencode.json"):
                app.write_opencode_config(gguf, 8080, 32768, None)
                config = json.loads((Path(tmp) / "opencode.json").read_text(encoding="utf-8"))
        self.assertNotIn("apiKey", config["provider"]["local-ai-starter"]["options"])


class StrataSupportedTests(unittest.TestCase):
    def test_mac(self):
        cases = [("15.0.0", True), ("26.2.0", True), ("14.7.1", False)]
        for version, expected in cases:
            with patch.object(app.platform, "system", return_value="Darwin"), \
                 patch.object(app.platform, "machine", return_value="arm64"), \
                 patch.object(app.platform, "mac_ver", return_value=(version, ("", ("", ""), ""), "")), \
                 patch.object(app, "is_apple_silicon", return_value=True):
                self.assertEqual(app.strata_supported(), expected, version)

    def test_intel_mac_is_unsupported(self):
        with patch.object(app.platform, "system", return_value="Darwin"), \
             patch.object(app.platform, "machine", return_value="x86_64"), \
             patch.object(app, "is_apple_silicon", return_value=False):
            self.assertFalse(app.strata_supported())

    def test_linux_and_windows(self):
        for system, machine, expected in (("Linux", "x86_64", True), ("Linux", "aarch64", True),
                                          ("Linux", "armv7l", False), ("Windows", "AMD64", True),
                                          ("Windows", "ARM64", False)):
            with patch.object(app.platform, "system", return_value=system), \
                 patch.object(app.platform, "machine", return_value=machine):
                self.assertEqual(app.strata_supported(), expected, (system, machine))


class StrataPlanTests(unittest.TestCase):
    def setUp(self):
        self.profile = app.PROFILES["qwen38-flash-next-q2_0"]

    def test_plan_is_parsed(self):
        result = app.subprocess.CompletedProcess([], 0)
        result.stdout = json.dumps({"ok": True, "plan": {"download": {"gb": 70.0, "engine_missing": True},
                                                         "warnings": []}})
        with patch.object(app, "strata_installed", return_value=True), \
             patch.object(app, "strata_control", return_value=result) as control:
            plan = app.strata_plan(self.profile)
        self.assertEqual(plan["download"]["gb"], 70.0)
        self.assertEqual(control.call_args[0][:5], ("launch", "--plan", "--family", "qwen", "--model"))

    def test_plan_failed_or_broken_returns_none(self):
        bad = app.subprocess.CompletedProcess([], 0)
        bad.stdout = json.dumps({"ok": False, "error": {"message": "no"}})
        broken = app.subprocess.CompletedProcess([], 0)
        broken.stdout = "{not json"
        with patch.object(app, "strata_installed", return_value=True), \
             patch.object(app, "strata_control", return_value=bad):
            self.assertIsNone(app.strata_plan(self.profile))
        with patch.object(app, "strata_installed", return_value=True), \
             patch.object(app, "strata_control", return_value=broken):
            self.assertIsNone(app.strata_plan(self.profile))
        with patch.object(app, "DRY_RUN", True), patch.object(app, "strata_control") as control:
            self.assertIsNone(app.strata_plan(self.profile))
            control.assert_not_called()

    def test_check_plan_allows_missing_engine_but_blocks_unusable(self):
        missing = {"download": {"engine_missing": True, "engine_usable": False}}
        usable = {"download": {"engine_missing": False, "engine_usable": True}, "warnings": []}
        broken = {"download": {"engine_missing": False, "engine_usable": False}, "warnings": ["card not supported"]}
        app.strata_check_plan(self.profile, missing)   # engine not downloaded yet: the launch fetches it
        app.strata_check_plan(self.profile, usable)
        with self.assertRaises(RuntimeError):
            app.strata_check_plan(self.profile, broken)


class StrataInstalledTests(unittest.TestCase):
    def setUp(self):
        self.profile = app.PROFILES["inkling-2-mini-sq10"]

    def test_match_by_family_and_model(self):
        entries = [{"family": "inkling-2-mini", "model": "SQ-10", "folder": "/x"}, {"family": "qwen", "model": "q2_0"}]
        with patch.object(app, "strata_models", return_value=entries):
            self.assertTrue(self.profile.installed)
        other = app.PROFILES["qwen38-flash-next-q2_0"]
        with patch.object(app, "strata_models", return_value=entries):
            self.assertTrue(other.installed)
        coder = app.PROFILES["qwen38-flash-next-coder"]
        with patch.object(app, "strata_models", return_value=entries):
            self.assertFalse(coder.installed)
        with patch.object(app, "strata_models", return_value=[]):
            self.assertFalse(self.profile.installed)

    def test_models_list_is_cached_and_failures_are_empty(self):
        with patch.object(app, "strata_installed", return_value=False):
            self.assertEqual(app.strata_models(refresh=True), [])
        good = app.subprocess.CompletedProcess([], 0)
        good.stdout = json.dumps({"models": [{"family": "inkling-2-mini", "model": "SQ-10"}]})
        with patch.object(app, "strata_installed", return_value=True), \
             patch.object(app, "strata_control", return_value=good):
            self.assertEqual(len(app.strata_models(refresh=True)), 1)
            with patch.object(app, "strata_control") as control:  # cached, no second call
                self.assertEqual(len(app.strata_models()), 1)
                control.assert_not_called()
        app._STRATA_MODELS = None


class StrataServerTests(unittest.TestCase):
    def test_dry_run_start_keeps_state_shape(self):
        profile = app.PROFILES["inkling-2-mini-sq10"]
        with patch.object(app, "DRY_RUN", True):
            state = app.start_strata(profile, 8080, 32768)
        self.assertEqual(state["engine"], "strata")
        self.assertEqual(state["model_id"], "strata")
        self.assertEqual(state["port"], 8080)
        self.assertTrue(state["api_key"])

    def test_stop_is_delegated_to_strata(self):
        state = {"engine": "strata", "port": 8080, "profile": "inkling-2-mini-sq10"}
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            with patch.object(app, "read_state", return_value=dict(state)), \
                 patch.object(app, "write_state") as write, \
                 patch.object(app, "is_healthy", side_effect=[True] + [False] * 20), \
                 patch.object(app, "strata_control") as control, \
                 patch.object(app, "DRY_RUN", False):
                app.stop_server()
            control.assert_called_once()
            self.assertEqual(control.call_args[0], ("launch", "--stop"))
            write.assert_called_once()
            self.assertNotIn("pid", write.call_args[0][0])

    def test_running_state_needs_health_for_strata(self):
        state = {"engine": "strata", "port": 8080, "profile": "inkling-2-mini-sq10"}
        with patch.object(app, "read_state", return_value=dict(state)), \
             patch.object(app, "is_healthy", return_value=True):
            self.assertEqual(app.running_state(), state)
        with patch.object(app, "read_state", return_value=dict(state)), \
             patch.object(app, "is_healthy", return_value=False):
            self.assertIsNone(app.running_state())


if __name__ == "__main__":
    unittest.main()
