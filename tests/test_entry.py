from __future__ import annotations

import ast
import binascii
import hashlib
import importlib.util
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets" / "entry.png"
MAIN = ROOT / "main.py"
RENDERER = ROOT / "tools" / "render_entry.py"
OUTPUT = Path("/output/entry.png")
MAX_BYTES = 1_048_576


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chunks(data: bytes):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError("missing PNG signature")
    position = 8
    result = []
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        kind = data[position + 4:position + 8]
        body = data[position + 8:position + 8 + length]
        crc = struct.unpack(">I", data[position + 8 + length:position + 12 + length])[0]
        result.append((kind, body, crc))
        position += 12 + length
    return result


def load_main_module():
    spec = importlib.util.spec_from_file_location("entry_main", MAIN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_main(cwd: Path):
    return subprocess.run(
        [sys.executable, "-I", str(MAIN)],
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=30,
    )


class ShippedPngTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = ASSET.read_bytes()
        cls.parts = chunks(cls.data)

    def test_chunk_crcs_are_valid_and_png_is_well_formed(self):
        self.assertEqual(self.parts[0][0], b"IHDR")
        self.assertEqual(self.parts[-1][0], b"IEND")
        for kind, body, stored_crc in self.parts:
            actual = binascii.crc32(kind + body) & 0xFFFFFFFF
            self.assertEqual(stored_crc, actual, f"bad CRC for {kind!r}")

    def test_exact_dimensions_and_rgb_mode(self):
        ihdr = self.parts[0][1]
        self.assertEqual(len(ihdr), 13)
        width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
            ">IIBBBBB", ihdr
        )
        self.assertEqual((width, height), (1024, 1024))
        self.assertEqual((depth, color_type), (8, 2))
        self.assertEqual((compression, filtering, interlace), (0, 0, 0))

    def test_image_data_decompresses_to_expected_scanlines(self):
        compressed = b"".join(body for kind, body, _ in self.parts if kind == b"IDAT")
        raw = zlib.decompress(compressed)
        self.assertEqual(len(raw), 1024 * (1 + 1024 * 3))
        stride = 1 + 1024 * 3
        self.assertTrue(all(raw[y * stride] <= 4 for y in range(1024)))

    def test_asset_size_limit(self):
        self.assertGreater(len(self.data), 100_000)
        self.assertLessEqual(len(self.data), MAX_BYTES)


class RuntimeTests(unittest.TestCase):
    def test_install_from_another_cwd_is_deterministic_and_exact(self):
        hashes = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temporary_directory:
                result = run_main(Path(temporary_directory))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(OUTPUT.is_file())
                self.assertEqual(OUTPUT.read_bytes(), ASSET.read_bytes())
                hashes.append(sha256(OUTPUT))
        self.assertEqual(hashes[0], hashes[1])
        self.assertEqual(hashes[0], sha256(ASSET))

    def test_missing_or_malformed_assets_fail_clearly(self):
        module = load_main_module()
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            missing = directory / "missing.png"
            destination = directory / "result.png"
            with self.assertRaisesRegex(module.EntryValidationError, "cannot read asset"):
                module.install(missing, destination)
            self.assertFalse(destination.exists())

            corrupt = bytearray(ASSET.read_bytes())
            corrupt[40] ^= 0x01
            with self.assertRaisesRegex(module.EntryValidationError, "CRC"):
                module.validate_png(bytes(corrupt))

            truncated = ASSET.read_bytes()[:-20]
            with self.assertRaises(module.EntryValidationError):
                module.validate_png(truncated)

    def test_runtime_uses_only_offline_standard_library(self):
        tree = ast.parse(MAIN.read_text())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        allowed = set(sys.stdlib_module_names)
        self.assertTrue(imported <= allowed, f"non-stdlib imports: {imported - allowed}")
        forbidden = {"socket", "ssl", "http", "urllib", "requests", "ftplib",
                     "smtplib", "telnetlib", "subprocess", "PIL"}
        self.assertFalse(imported & forbidden)


class RendererTests(unittest.TestCase):
    def test_renderer_reproduces_the_shipped_asset(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "entry.png"
            result = subprocess.run(
                [sys.executable, str(RENDERER), "--out", str(target)],
                cwd=temporary_directory,
                text=True,
                capture_output=True,
                timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(sha256(target), sha256(ASSET))

    def test_editorial_copy_keeps_required_attribution_and_status(self):
        spec = importlib.util.spec_from_file_location("entry_renderer", RENDERER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        lines = module.STORY_LINES
        self.assertIn("Houthi", lines["lead_body"])
        self.assertIn("no independent confirmation", lines["lead_body"].lower())
        self.assertIn("fossil fuels", lines["cop31_body"])
        self.assertIn("NO FINAL DEAL", lines["cop31_status"])
        self.assertEqual(lines["korea_status"], "STATE MEDIA REPORT / 21 NOV")
        self.assertIn("Friday", lines["iran_body"])
        self.assertEqual(lines["dragon_status"], "SCHEDULED / NOT YET CONFIRMED")
        self.assertIn("4:55pm EST", lines["dragon_body"])
        source = RENDERER.read_text()
        for required in ("21 NOV 2026", "03:45 UTC", "EARLY EDITION"):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
