import dataclasses
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import local_ai_starter as app


class CustomProfilesTest(unittest.TestCase):
    def test_resolve_persist_and_reload_nested_file(self):
        metadata = {"sha": "a" * 40, "siblings": [{"rfilename": "sub/model.gguf", "size": 123,
                    "lfs": {"sha256": "b" * 64}}]}
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, "ROOT", Path(tmp)), \
                patch.object(app, "STATE_FILE", Path(tmp) / "state.json"), \
                patch.object(app, "http_json", return_value=(200, metadata)):
            profile = app.custom_profile("https://huggingface.co/a/b/blob/main/sub/model.gguf")
            self.assertIn("/resolve/" + "a" * 40 + "/sub/model.gguf", profile.url)
            app.write_state({"custom_profiles": [dataclasses.asdict(profile)], "profile": profile.key})
            with patch.dict(app.PROFILES, {}, clear=True):
                app.load_custom_profiles()
                self.assertEqual(app.saved_profile().sha256, "b" * 64)
                self.assertEqual(app.saved_profile().path.name, "model.gguf")

    def test_rejects_invalid_and_multipart_links(self):
        for url in ("https://evil.test/a/b/resolve/main/a.gguf",
                    "https://huggingface.co/a/b/resolve/main/mmproj-a.gguf",
                    "https://huggingface.co/a/b/resolve/main/a-00001-of-00002.gguf",
                    "https://huggingface.co/a/b/resolve/main/../a.gguf"):
            with self.subTest(url=url), self.assertRaises(RuntimeError):
                app.custom_profile(url)

    def test_token_is_not_forwarded_as_regular_header(self):
        request = app.urllib.request.Request("https://huggingface.co/a/b")
        with patch.dict(os.environ, {"HF_TOKEN": "secret"}):
            app.hf_authorize(request)
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(request.unredirected_hdrs["Authorization"], "Bearer secret")


class UpdateTest(unittest.TestCase):
    def git(self, directory, *args):
        return subprocess.run(["git", "-c", "commit.gpgsign=false", "-C", str(directory), *args], check=True,
                              capture_output=True, text=True)

    def test_untracked_files_survive_and_tracked_changes_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote, work, producer = root / "remote.git", root / "work", root / "producer"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            subprocess.run(["git", "clone", str(remote), str(producer)], check=True, capture_output=True)
            self.git(producer, "config", "user.email", "test@example.invalid")
            self.git(producer, "config", "user.name", "Test")
            (producer / "file").write_text("old")
            self.git(producer, "add", "file")
            self.git(producer, "commit", "-m", "first")
            self.git(producer, "push", "origin", "HEAD")
            subprocess.run(["git", "clone", str(remote), str(work)], check=True, capture_output=True)
            (producer / "file").write_text("new")
            self.git(producer, "commit", "-am", "second")
            self.git(producer, "tag", "v9.9.9")
            self.git(producer, "push", "origin", "HEAD", "--tags")
            (work / "test-runs").mkdir()
            (work / "test-runs" / "result").write_text("keep")
            with patch.object(app, "APP_DIR", work):
                self.assertTrue(app._update_git("v9.9.9"))
                self.assertEqual((work / "test-runs" / "result").read_text(), "keep")
                (work / "file").write_text("local")
                self.assertFalse(app._update_git("v9.9.9"))
                self.assertEqual((work / "file").read_text(), "local")


class MediaTest(unittest.TestCase):
    def test_i2v_command_includes_both_experts_and_input(self):
        profile = app.PROFILES["wan2.2-i2v-14b"]
        command = app.media_command(profile, "move", Path("out.webm"), {"-i": "/tmp/my image.png"})
        for flag in ("--diffusion-model", "--high-noise-diffusion-model", "--vae", "--t5xxl", "-i"):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index("-i") + 1], "/tmp/my image.png")


class StateSafetyTest(unittest.TestCase):
    def test_migration_keeps_media_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / "models"
            for family in ("sd", "tts", "old-family"):
                (models / family).mkdir(parents=True)
                (models / family / "weights").write_text(family)
            with patch.object(app, "ROOT", root), patch.object(app, "MODELS_DIR", models), \
                    patch.object(app, "LLAMA_DIR", root / "engines" / "llama"), patch.object(app, "DRY_RUN", False):
                app.migrate_layout()
            self.assertTrue((models / "sd" / "weights").exists())
            self.assertTrue((models / "tts" / "weights").exists())
            self.assertTrue((models / "gguf" / "old-family" / "weights").exists())

    def test_selected_model_does_not_replace_live_server_identity(self):
        profile = app.PROFILES["qwen3.5-4b"]
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, "ROOT", Path(tmp)), \
                patch.object(app, "STATE_FILE", Path(tmp) / "state.json"), \
                patch.object(app, "engine_installed", return_value=True), \
                patch.object(app, "opencode_binary", return_value=Path("opencode")), \
                patch.object(app.Profile, "installed", new_callable=lambda: property(lambda self: True)):
            app.write_state({"pid": 123, "profile": "previous"})
            app.ensure_installed(profile)
            self.assertEqual(app.read_state()["server_profile"], "previous")
            with patch.object(app, "running_state", return_value=app.read_state()), \
                    patch.object(app, "stop_server") as stop, \
                    patch.object(app, "pick_port", return_value=8080), \
                    patch.object(app, "start_server", return_value={}), patch.object(app, "wait_ready"):
                app.bring_up(profile)
                stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
