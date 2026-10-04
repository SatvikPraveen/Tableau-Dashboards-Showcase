import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import paths, verify_data


class VerifyDataTests(unittest.TestCase):
    def test_committed_data_passes_every_check(self):
        for check in (verify_data.check_checksums, verify_data.check_mortality, verify_data.check_spending):
            with self.subTest(check=check.__name__):
                failed = [label for label, ok, _ in check() if not ok]
                self.assertEqual(failed, [])

    def test_checksum_check_detects_a_modified_file(self):
        """Negative control: a single changed byte must fail verification."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relative = paths.MORTALITY_CSV.relative_to(paths.REPO_ROOT)
            copy = root / relative
            copy.parent.mkdir(parents=True)
            shutil.copy(paths.MORTALITY_CSV, copy)
            with open(copy, "ab") as handle:
                handle.write(b" ")
            manifest = root / "CHECKSUMS.sha256"
            expected = verify_data.sha256(paths.MORTALITY_CSV)
            manifest.write_text(f"# comment\n{expected}  {relative.as_posix()}\n", encoding="utf-8")
            with mock.patch.object(paths, "REPO_ROOT", root), mock.patch.object(paths, "CHECKSUMS", manifest):
                results = verify_data.check_checksums()
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][1])

    def test_checksum_check_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "CHECKSUMS.sha256"
            manifest.write_text("0" * 64 + "  does/not/exist.csv\n", encoding="utf-8")
            with mock.patch.object(paths, "CHECKSUMS", manifest):
                ((label, ok, detail),) = verify_data.check_checksums()
        self.assertFalse(ok)
        self.assertEqual(detail, "file missing")


if __name__ == "__main__":
    unittest.main()
