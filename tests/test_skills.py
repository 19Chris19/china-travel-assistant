import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins" / "china-travel-assistant" / "skills"
EXPECTED = {
    "plan-china-trip",
    "search-china-flights",
    "search-china-trains",
    "plan-china-transfers",
    "search-china-hotels",
    "verify-travel-web",
    "explore-china-routes",
    "present-china-trip",
}


class SkillTests(unittest.TestCase):
    def test_expected_skills_have_valid_minimal_frontmatter(self):
        self.assertEqual({path.name for path in SKILLS.iterdir() if path.is_dir()}, EXPECTED)
        for name in EXPECTED:
            skill = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(skill.startswith("---\n"), name)
            header = skill.split("---", 2)[1]
            self.assertIn(f"name: {name}\n", header)
            self.assertRegex(header, r"description: .{80,}")
            self.assertNotIn("TODO", skill)
            self.assertLess(len(skill.splitlines()), 500)

    def test_local_markdown_references_exist(self):
        pattern = re.compile(r"\[[^]]+\]\((?!https?://)([^)#]+)(?:#[^)]+)?\)")
        for skill_path in SKILLS.glob("*/SKILL.md"):
            text = skill_path.read_text(encoding="utf-8")
            for target in pattern.findall(text):
                self.assertTrue((skill_path.parent / target).exists(), f"missing {target} from {skill_path}")

    def test_only_web_verification_skill_contains_browser_commands(self):
        for skill_path in SKILLS.glob("*/SKILL.md"):
            text = skill_path.read_text(encoding="utf-8").lower()
            if skill_path.parent.name == "verify-travel-web":
                self.assertIn("ego-browser nodejs", text)
                self.assertIn("handoff", text.replace("hand off", "handoff"))
            else:
                self.assertNotIn("ego-browser nodejs", text)

    def test_every_transactional_domain_has_a_confirmation_boundary(self):
        for name in ("plan-china-trip", "search-china-flights", "search-china-trains", "search-china-hotels"):
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8").lower()
            self.assertTrue("confirm" in text or "confirmation" in text, name)
            self.assertTrue("payment" in text or "pay" in text, name)

    def test_openai_metadata_exists_and_names_the_skill(self):
        for name in EXPECTED:
            metadata = (SKILLS / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn(f"${name}", metadata)
            self.assertNotIn("TODO", metadata)

    def test_parent_skill_orchestrates_exploration_and_presentation(self):
        text = (SKILLS / "plan-china-trip" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("$explore-china-routes", text)
        self.assertIn("$present-china-trip", text)
        self.assertIn("Never enable Pro Max without an explicit user choice", text)

    def test_exploration_tiers_share_high_baseline_capabilities(self):
        text = (SKILLS / "explore-china-routes" / "SKILL.md").read_text(encoding="utf-8")
        for capability in ("student fares", "accommodation", "luggage", "taxes", "refund"):
            self.assertIn(capability, text)
        self.assertIn("Pro Max", text)
        self.assertIn("explicit", text)

    def test_presentation_skill_keeps_image_generation_out_of_facts(self):
        text = (SKILLS / "present-china-trip" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Visualize", text)
        self.assertIn("itinerary.json", text)
        self.assertIn("ImageGen must not", text)

    def test_parent_skill_explains_generic_gateways_weather_and_safe_health(self):
        text = (SKILLS / "plan-china-trip" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("GatewayCandidate", text)
        self.assertIn("QWeather", text)
        self.assertIn("provider-health", text)
        self.assertIn("Do not hard-code a city, airport", text)


if __name__ == "__main__":
    unittest.main()
