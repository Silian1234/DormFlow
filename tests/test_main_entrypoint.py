from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

import main


class MainEntrypointTests(unittest.TestCase):
    def test_backend_help_uses_main_entrypoint(self):
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised:
            with redirect_stdout(output):
                main.main(["backend", "--help"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("Run DormFlow backend API", output.getvalue())


if __name__ == "__main__":
    unittest.main()
