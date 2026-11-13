import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import local_ai_starter as app


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.env = patch.dict(os.environ, {"HOME": str(self.root), "XDG_CONFIG_HOME": str(self.root / "config"),
                                         "CLAUDE_CONFIG_DIR": str(self.root / ".claude"),
                                         "CODEX_HOME": str(self.root / ".codex")})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.local = patch.object(app, "OPENCODE_HOME", self.root / "isolated")
        self.local.start()
        self.addCleanup(self.local.stop)
        self.dry = patch.object(app, "DRY_RUN", False)
        self.dry.start()
        self.addCleanup(self.dry.stop)

    def put(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_global_both_and_existing(self):
        source = self.root / ".claude" / "CLAUDE.md"
        self.put(source, "instructions")
        existing = self.root / ".codex" / "AGENTS.md"
        self.put(existing, "keep")
        plan = app.transfer_plan("claude", [("codex", False), ("opencode", False), ("opencode", True)], [], True)
        self.assertEqual(app.transfer_apply(plan), (2, 1))
        self.assertEqual(existing.read_text(), "keep")
        self.assertEqual((self.root / "config/opencode/AGENTS.md").read_text(), "instructions")
        self.assertEqual((self.root / "isolated/config/opencode/AGENTS.md").read_text(), "instructions")
        self.assertEqual(app.transfer_apply(plan), (0, 3))

    def test_project_skills_commands_and_reverse(self):
        project = self.root / "project"
        self.put(project / "CLAUDE.md", "project")
        self.put(project / ".claude/skills/review/SKILL.md", "skill")
        self.put(project / ".claude/commands/review.md", "Review $ARGUMENTS")
        self.put(project / ".claude/commands/specific.md", "---\nmodel: x\n---\ntext")
        plan = app.transfer_plan("claude", [("codex", False), ("opencode", False)], [project], False)
        app.transfer_apply(plan)
        self.assertEqual((project / "AGENTS.md").read_text(), "project")
        self.assertTrue((project / ".agents/skills/review/SKILL.md").exists())
        self.assertTrue((project / ".opencode/commands/review.md").exists())
        self.assertFalse((project / ".opencode/commands/specific.md").exists())
        reverse = app.transfer_plan("codex", [("claude", False)], [project], False)
        self.assertIn((project / "AGENTS.md", project / "CLAUDE.md"), reverse)

    def test_symlinks_and_override(self):
        project = self.root / "project"
        self.put(project / "CLAUDE.md", "source")
        self.put(project / "AGENTS.override.md", "override")
        plan = app.transfer_plan("claude", [("codex", False)], [project], False)
        self.assertFalse(any(dest.name == "AGENTS.md" for _, dest in plan))
        outside = self.root / "outside"
        outside.mkdir()
        (project / ".opencode").symlink_to(outside, target_is_directory=True)
        self.put(project / ".claude/commands/test.md", "test")
        plan = app.transfer_plan("claude", [("opencode", False)], [project], False)
        app.transfer_apply(plan)
        self.assertFalse((outside / "commands/test.md").exists())


if __name__ == "__main__":
    unittest.main()
