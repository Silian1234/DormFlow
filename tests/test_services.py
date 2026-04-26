from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dormflow.models import IssueStatus, UserRole
from dormflow.services import DormFlowService


class DormFlowServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.tmp_dir.name) / "state.json"
        self.service = DormFlowService(storage_path=self.storage)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_seed_created(self):
        self.assertTrue(self.storage.exists())
        self.assertGreaterEqual(len(self.service.list_duties()), 1)
        self.assertGreaterEqual(len(self.service.list_issues()), 1)

    def test_switch_role(self):
        self.service.switch_role(UserRole.HEADMAN)
        self.assertEqual(self.service.get_profile().role, UserRole.HEADMAN)

    def test_issue_lifecycle(self):
        issue = self.service.create_issue("Тест", "Описание", "Другое")
        self.assertEqual(issue.status, IssueStatus.NEW)
        moved = self.service.move_issue_status(issue.issue_id)
        self.assertEqual(moved.status, IssueStatus.IN_PROGRESS)
        moved = self.service.move_issue_status(issue.issue_id)
        self.assertEqual(moved.status, IssueStatus.DONE)

    def test_vote_only_once(self):
        poll = self.service.list_polls()[0]
        ok1 = self.service.vote(poll.poll_id, 0)
        ok2 = self.service.vote(poll.poll_id, 1)
        self.assertTrue(ok1)
        self.assertFalse(ok2)


if __name__ == "__main__":
    unittest.main()

