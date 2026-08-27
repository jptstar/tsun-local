from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]


class Play2BetaCommunicationTests(unittest.TestCase):
    def test_02b0_declares_clear_text_alarm_entities(self) -> None:
        source = (ROOT / "custom_components/tsun_local/protocols/protocol_02b0.py").read_text(encoding="utf-8")
        self.assertIn('"alarm_active_count"', source)
        self.assertIn('"active_alarm_names"', source)
        self.assertIn('SENSOR_LIST = 0x02B0', source)

    def test_public_docs_mark_play2_validated(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        entities = (ROOT / "docs/ENTITIES.md").read_text(encoding="utf-8")
        self.assertIn('`Sunology PLAY2`', readme)
        self.assertIn('Sunology PLAY2 is validated on real Home Assistant hardware', readme)
        self.assertIn('TSOL-MX500 and Sunology PLAY2', entities)

    def test_web_metadata_mentions_play2(self) -> None:
        site = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn('Sunology PLAY2', site)
        self.assertIn('Sunology Play 2', site)
        self.assertIn('clear-text alarms', site)


if __name__ == "__main__":
    unittest.main()
