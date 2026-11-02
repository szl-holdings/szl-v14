from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


BUILD_PATH = Path(__file__).resolve().parents[1] / "build.py"
SPEC = importlib.util.spec_from_file_location("payload_builder_build", BUILD_PATH)
assert SPEC is not None and SPEC.loader is not None
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class BuilderPublicationEligibilityTests(unittest.TestCase):
    def test_missing_or_literal_false_stays_false(self) -> None:
        self.assertIs(BUILD.builder_publication_eligible({}), False)
        self.assertIs(
            BUILD.builder_publication_eligible(
                {"gates": {"publication_eligible": False}}
            ),
            False,
        )

    def test_boolean_lookalikes_and_true_are_rejected(self) -> None:
        for value in (True, "false", "true", 0, 1, None, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit) as raised:
                    BUILD.builder_publication_eligible(
                        {"gates": {"publication_eligible": value}}
                    )
                self.assertEqual(raised.exception.code, 1)

    def test_gates_must_be_a_table(self) -> None:
        for value in (None, False, "", []):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit) as raised:
                    BUILD.builder_publication_eligible({"gates": value})
                self.assertEqual(raised.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
