import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from china_travel_assistant.cli import main
from china_travel_assistant.contracts import PresentationMode
from china_travel_assistant.presentation import render_plan


def sample_plan():
    return {
        "request": {
            "origin": "沈阳<script>",
            "destination": "苏州",
            "date_start": "2026-08-30",
        },
        "resolved_tier": "pro",
        "itineraries": [
            {
                "itinerary_id": "route-001",
                "title": "G1234 稳妥路线",
                "tier": "pro",
                "is_baseline": True,
                "total_price_cny": 730,
                "total_duration_minutes": 600,
                "transfer_count": 0,
                "risk_level": "stable",
                "evidence_status": "verified",
                "benefit_summary": None,
                "burden_summary": "无自助换乘",
                "delay_fallback": "铁路保护换乘",
                "unknown_fields": ["refund_change"],
                "legs": [
                    {
                        "leg_id": "g1",
                        "mode": "train",
                        "origin": "沈阳站",
                        "destination": "苏州站",
                        "service_number": "G1234",
                        "departure_at": "2026-08-30T12:00:00+08:00",
                        "arrival_at": "2026-08-30T22:00:00+08:00",
                        "total_price_cny": 730,
                        "buffer_minutes": 45,
                        "booking_url": "https://www.12306.cn/index/",
                        "evidence_status": "verified",
                        "sources": ["12306"],
                    }
                ],
            }
        ],
    }


class PresentationTests(unittest.TestCase):
    def test_html_is_self_contained_exact_and_escapes_untrusted_text(self):
        mode, rendered = render_plan(sample_plan(), PresentationMode.HTML)

        self.assertEqual(mode, PresentationMode.HTML)
        self.assertIn("G1234", rendered)
        self.assertIn("CNY 730.00", rendered)
        self.assertIn("2026-08-30T12:00:00+08:00", rendered)
        self.assertIn("沈阳&lt;script&gt;", rendered)
        self.assertNotIn("沈阳<script>", rendered)
        self.assertNotRegex(rendered, r"<(?:script|iframe)\b")
        self.assertNotRegex(rendered, r"(?:src|href)=[\"']https?://(?!www\.12306\.cn/index/)")
        self.assertIn("<details", rendered)
        self.assertIn("prefers-color-scheme:dark", rendered)

    def test_svg_is_valid_and_preserves_unknowns(self):
        plan = sample_plan()
        plan["itineraries"][0]["total_price_cny"] = None
        mode, rendered = render_plan(plan, PresentationMode.SVG)

        self.assertEqual(mode, PresentationMode.SVG)
        root = ET.fromstring(rendered)
        self.assertEqual(root.tag.rsplit("}", 1)[-1], "svg")
        self.assertIn("未返回", rendered)
        self.assertIn("G1234", rendered)

    def test_markdown_keeps_booking_link_and_risk(self):
        mode, rendered = render_plan(sample_plan(), PresentationMode.MARKDOWN)

        self.assertEqual(mode, PresentationMode.MARKDOWN)
        self.assertIn("https://www.12306.cn/index/", rendered)
        self.assertIn("风险: stable", rendered)
        self.assertIn("事实源: `itinerary.json`", rendered)

    def test_auto_local_fallback_is_html_and_visualize_requires_host(self):
        mode, _ = render_plan(sample_plan(), PresentationMode.AUTO)
        self.assertEqual(mode, PresentationMode.HTML)
        with self.assertRaisesRegex(ValueError, "Agent host"):
            render_plan(sample_plan(), PresentationMode.VISUALIZE)

    def test_cli_writes_rendered_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "trip.html"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = main(
                    [
                        "render-plan",
                        json.dumps(sample_plan()),
                        "--format",
                        "html",
                        "--output",
                        str(output_path),
                    ]
                )

            self.assertEqual(result, 0, stderr.getvalue())
            self.assertTrue(output_path.is_file())
            self.assertIn("G1234", output_path.read_text(encoding="utf-8"))
            receipt = json.loads(stdout.getvalue())
            self.assertEqual(receipt["format"], "html")
            self.assertEqual(receipt["output"], str(output_path))


if __name__ == "__main__":
    unittest.main()
