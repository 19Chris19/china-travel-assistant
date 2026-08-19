import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "china-travel-assistant" / "skills" / "plan-china-trip" / "scripts" / "validate_plan.py"


class PlanValidatorTests(unittest.TestCase):
    def run_validator(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / "plan.json"
            plan.write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(plan)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_accepts_plan_with_explicit_leg_totals_and_buffers(self):
        result = self.run_validator(
            {
                "request": {"origin": "沈阳", "destination": "苏州", "date_start": "2026-08-20"},
                "offers": [{"provider": "flyai", "mode": "flight", "total_price_cny": 550}],
                "transfers": [
                    {
                        "origin": "浦东机场",
                        "destination": "上海虹桥站",
                        "mode": "metro",
                        "duration_minutes": 95,
                        "buffer_minutes": 30,
                        "cost_cny": 8,
                    }
                ],
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["known_total_cny"], 558)
        self.assertEqual(report["status"], "valid")

    def test_rejects_missing_request_or_negative_values(self):
        missing = self.run_validator({"offers": [], "transfers": []})
        negative = self.run_validator(
            {
                "request": {"origin": "沈阳", "destination": "苏州", "date_start": "2026-08-20"},
                "offers": [{"provider": "flyai", "mode": "flight", "total_price_cny": -1}],
                "transfers": [],
            }
        )

        self.assertEqual(missing.returncode, 2)
        self.assertEqual(negative.returncode, 2)


if __name__ == "__main__":
    unittest.main()
