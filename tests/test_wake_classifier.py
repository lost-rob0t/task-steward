from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("classify_wake", ROOT / "scripts" / "classify_wake.py")
classifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(classifier)


class WakeClassifierTests(unittest.TestCase):
    def test_explicit_wake_commit_evaluates_once(self):
        decision = classifier.classify("push", "[steward-wake] reevaluate durable state")
        self.assertTrue(decision.evaluate)
        self.assertEqual(decision.reason, "explicit_steward_wake")

    def test_state_commit_never_recurses(self):
        decision = classifier.classify("push", "[steward-state] persist observation")
        self.assertFalse(decision.evaluate)
        self.assertEqual(decision.reason, "self_generated_state_commit")

    def test_ordinary_main_push_is_validation_only(self):
        decision = classifier.classify("push", "merge issue slice")
        self.assertFalse(decision.evaluate)
        self.assertEqual(decision.reason, "ordinary_push_validation_only")

    def test_pull_request_is_validation_only(self):
        self.assertFalse(classifier.classify("pull_request", "[steward-wake]").evaluate)

    def test_manual_dispatch_evaluates(self):
        self.assertTrue(classifier.classify("workflow_dispatch").evaluate)

    def test_dual_markers_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "both"):
            classifier.classify("push", "[steward-wake] [steward-state]")

    def test_unknown_event_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unsupported"):
            classifier.classify("schedule", "")


if __name__ == "__main__":
    unittest.main()
