import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "mgpu_profile", Path(__file__).resolve().parents[1] / "scripts/mgpu_profile.py")
profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile)


class ProfileTests(unittest.TestCase):
    def test_atomic_sr_pair_and_unrelated_state(self):
        raw = b"[MGPU]\nSRScale=67\nSRMvLowRes=1\nIntensity=2.0\nArmCrashed=1\nMonitor=ASUS\n"
        result = profile.render(raw, "native-upscale")
        for value in (b"SRUpscale=1", b"SRScale=0", b"SRMvLowRes=0",
                      b"Intensity=2.0", b"ArmCrashed=1", b"Monitor=ASUS"):
            self.assertIn(value, result)

    def test_native_disables_sr(self):
        self.assertIn(b"SRUpscale=0", profile.render(b"[MGPU]\n", "native"))

    def test_other_sections_bom_crlf_comments(self):
        raw = b"\xef\xbb\xbf[MGPU]\r\nPasses=4 ; keep\r\n[Other]\r\nPasses=9\r\n"
        result = profile.render(raw, "native")
        self.assertTrue(result.startswith(b"\xef\xbb\xbf"))
        self.assertIn(b"Passes=1; keep\r\n", result)
        self.assertTrue(result.endswith(b"[Other]\r\nPasses=9\r\n"))
        self.assertNotIn(b"\n", result.replace(b"\r\n", b""))

    def test_ambiguous_or_invalid_input(self):
        for raw in (b"[Other]\n", b"[MGPU]\n[mgpu]\n",
                    b"[MGPU]\nPasses=1\npasses=2\n", b"[MGPU]\n\x00"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                profile.render(raw, "native")

    def test_idempotence(self):
        once = profile.render(b"[MGPU]", "native-upscale")
        self.assertEqual(once, profile.render(once, "native-upscale"))

    def test_preview_backup_and_restore(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            path = Path(directory) / "mgpu.ini"
            raw = b"[MGPU]\r\nPasses=4\r\n"
            path.write_bytes(raw)
            profile.apply(path, "native-upscale", True)
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(len(list(path.parent.iterdir())), 1)
            profile.apply(path, "native-upscale", False)
            backup, = path.parent.glob("mgpu.ini.backup-*")
            self.assertEqual(backup.read_bytes(), raw)
            profile.apply(path, "native-upscale", False)
            self.assertEqual(len(list(path.parent.glob("mgpu.ini.backup-*"))), 1)
            path.write_bytes(backup.read_bytes())
            self.assertEqual(path.read_bytes(), raw)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mgpu.ini"
            target = Path(directory) / "target"
            target.write_bytes(b"[MGPU]\n")
            path.symlink_to(target)
            with self.assertRaises(ValueError):
                profile.apply(path, "native", False)


if __name__ == "__main__":
    unittest.main()
