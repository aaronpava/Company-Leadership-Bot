"""
Tests for Company Leadership Bot.

These tests validate the persona definitions and core bot logic without
requiring an OpenAI API key (demo mode).
"""

import sys
import os
import unittest
from unittest.mock import patch

# Ensure repo root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPersonas(unittest.TestCase):
    """Validate the twelve leadership personas."""

    def setUp(self):
        from personas import PERSONAS
        self.personas = PERSONAS

    def test_exactly_twelve_personas(self):
        self.assertEqual(len(self.personas), 12, "There must be exactly twelve leadership personas.")

    def test_each_persona_has_required_keys(self):
        required_keys = {"id", "title", "name", "background", "priorities", "style"}
        for persona in self.personas:
            with self.subTest(persona=persona.get("id", "unknown")):
                self.assertTrue(
                    required_keys.issubset(persona.keys()),
                    f"Persona {persona.get('id')} missing keys: {required_keys - persona.keys()}",
                )

    def test_each_persona_has_unique_id(self):
        ids = [p["id"] for p in self.personas]
        self.assertEqual(len(ids), len(set(ids)), "All persona IDs must be unique.")

    def test_each_persona_has_unique_title(self):
        titles = [p["title"] for p in self.personas]
        self.assertEqual(len(titles), len(set(titles)), "All persona titles must be unique.")

    def test_each_persona_has_at_least_three_priorities(self):
        for persona in self.personas:
            with self.subTest(persona=persona["id"]):
                self.assertGreaterEqual(
                    len(persona["priorities"]),
                    3,
                    f"Persona {persona['id']} should have at least 3 priorities.",
                )

    def test_each_persona_has_non_empty_background(self):
        for persona in self.personas:
            with self.subTest(persona=persona["id"]):
                self.assertTrue(
                    len(persona["background"].strip()) > 20,
                    f"Persona {persona['id']} has a too-short background.",
                )

    def test_each_persona_has_non_empty_style(self):
        for persona in self.personas:
            with self.subTest(persona=persona["id"]):
                self.assertTrue(
                    len(persona["style"].strip()) > 20,
                    f"Persona {persona['id']} has a too-short style description.",
                )

    def test_expected_leadership_roles_present(self):
        """Key leadership roles should be represented."""
        ids = {p["id"] for p in self.personas}
        expected_ids = {
            "ceo", "cto", "cfo", "coo",
            "vp_bizdev", "vp_engineering",
            "chief_of_staff",
            "director_drupal", "director_open_data",
            "director_opensource", "director_federal_delivery",
            "director_people",
        }
        self.assertEqual(ids, expected_ids, f"Missing or unexpected persona IDs: {ids.symmetric_difference(expected_ids)}")

    def test_drupal_expertise_represented(self):
        """Company's Drupal specialization must be reflected in at least one persona."""
        drupal_personas = [
            p for p in self.personas
            if "drupal" in p["background"].lower() or "drupal" in p["title"].lower()
        ]
        self.assertGreater(len(drupal_personas), 0, "At least one persona must reflect Drupal expertise.")

    def test_open_data_represented(self):
        """Company's open data focus must be reflected in at least one persona."""
        open_data_personas = [
            p for p in self.personas
            if "open data" in p["background"].lower() or "open data" in p["title"].lower()
        ]
        self.assertGreater(len(open_data_personas), 0, "At least one persona must reflect open data expertise.")

    def test_open_source_represented(self):
        """Company's open-source focus must be reflected in at least one persona."""
        oss_personas = [
            p for p in self.personas
            if "open source" in p["background"].lower() or "open source" in p["title"].lower()
            or "open-source" in p["background"].lower()
        ]
        self.assertGreater(len(oss_personas), 0, "At least one persona must reflect open-source expertise.")

    def test_federal_focus_represented(self):
        """Federal agency context must be reflected in backgrounds."""
        federal_personas = [
            p for p in self.personas
            if "federal" in p["background"].lower()
        ]
        self.assertGreater(len(federal_personas), 5, "Most personas should reflect federal contracting context.")


class TestDemoMode(unittest.TestCase):
    """Test bot logic in demo mode (no API key required)."""

    def setUp(self):
        import bot
        self.bot = bot
        from personas import PERSONAS
        self.personas = PERSONAS

    def test_get_demo_perspective_returns_string(self):
        persona = self.personas[0]
        result = self.bot.get_demo_perspective(persona, "Should we pursue AI-assisted Drupal development?")
        self.assertIsInstance(result, str)
        self.assertIn("[DEMO MODE", result)

    def test_get_demo_perspective_includes_persona_title(self):
        persona = self.personas[0]
        topic = "Should we bid on a CMS consolidation contract?"
        result = self.bot.get_demo_perspective(persona, topic)
        self.assertIn(persona["title"], result)

    def test_get_demo_perspective_includes_top_priority(self):
        persona = self.personas[2]  # CFO
        topic = "Should we invest in a new open data practice?"
        result = self.bot.get_demo_perspective(persona, topic)
        self.assertIn(persona["priorities"][0], result)

    def test_get_demo_synthesis_returns_string(self):
        result = self.bot.get_demo_synthesis("Expand headless Drupal services?", self.personas)
        self.assertIsInstance(result, str)
        self.assertIn("[DEMO MODE", result)

    def test_get_demo_synthesis_includes_recommended_steps(self):
        result = self.bot.get_demo_synthesis("New IDIQ vehicle?", self.personas)
        self.assertIn("next steps", result.lower())

    def test_build_system_prompt_includes_persona_title(self):
        persona = self.personas[1]  # CTO
        prompt = self.bot.build_system_prompt(persona)
        self.assertIn(persona["title"], prompt)

    def test_build_system_prompt_includes_priorities(self):
        persona = self.personas[1]  # CTO
        prompt = self.bot.build_system_prompt(persona)
        for priority in persona["priorities"]:
            self.assertIn(priority, prompt)

    def test_build_system_prompt_includes_company_context(self):
        persona = self.personas[0]
        prompt = self.bot.build_system_prompt(persona)
        self.assertIn("Drupal", prompt)
        self.assertIn("federal", prompt.lower())

    def test_facilitate_discussion_demo_mode_runs_without_error(self):
        """Full demo-mode run should complete without raising exceptions."""
        with patch("builtins.print"), patch.dict(os.environ, {}, clear=True):
            self.bot.facilitate_discussion(
                topic="Should Company invest in an AI-assisted code review tool?",
                rounds=1,
                output_file=None,
                skip_synthesis=False,
            )

    def test_facilitate_discussion_with_output_file(self):
        """Demo mode should write a Markdown report when output_file is specified."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            tmp_path = f.name

        try:
            with patch("builtins.print"), patch.dict(os.environ, {}, clear=True):
                self.bot.facilitate_discussion(
                    topic="Open source vs. proprietary for federal portals?",
                    rounds=1,
                    output_file=tmp_path,
                    skip_synthesis=True,
                )
            with open(tmp_path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Leadership", content)
            self.assertIn("Open source vs. proprietary", content)
        finally:
            os.unlink(tmp_path)

    def test_facilitate_discussion_two_rounds(self):
        """Two-round discussion should not raise errors in demo mode."""
        with patch("builtins.print"), patch.dict(os.environ, {}, clear=True):
            self.bot.facilitate_discussion(
                topic="Should we expand our open data practice?",
                rounds=2,
                output_file=None,
                skip_synthesis=True,
            )

    def test_list_personas_does_not_raise(self):
        """list_personas() should run without error when rich is unavailable."""
        with patch.object(self.bot, "RICH_AVAILABLE", False), patch("builtins.print"):
            self.bot.list_personas()


class TestCLIArgParsing(unittest.TestCase):
    """Test argument parsing for the CLI."""

    def setUp(self):
        import bot
        self.bot = bot

    def test_default_rounds_is_one(self):
        with patch("sys.argv", ["bot.py"]):
            args = self.bot.parse_args()
        self.assertEqual(args.rounds, 1)

    def test_custom_topic_parsed(self):
        with patch("sys.argv", ["bot.py", "--topic", "Should we use headless Drupal?"]):
            args = self.bot.parse_args()
        self.assertEqual(args.topic, "Should we use headless Drupal?")

    def test_rounds_parsed(self):
        with patch("sys.argv", ["bot.py", "--topic", "Test", "--rounds", "3"]):
            args = self.bot.parse_args()
        self.assertEqual(args.rounds, 3)

    def test_no_synthesis_flag(self):
        with patch("sys.argv", ["bot.py", "--topic", "Test", "--no-synthesis"]):
            args = self.bot.parse_args()
        self.assertTrue(args.no_synthesis)

    def test_output_flag(self):
        with patch("sys.argv", ["bot.py", "--topic", "Test", "--output", "out.md"]):
            args = self.bot.parse_args()
        self.assertEqual(args.output, "out.md")

    def test_list_personas_flag(self):
        with patch("sys.argv", ["bot.py", "--list-personas"]):
            args = self.bot.parse_args()
        self.assertTrue(args.list_personas)


if __name__ == "__main__":
    unittest.main()
