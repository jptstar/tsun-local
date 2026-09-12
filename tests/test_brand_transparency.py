# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify TSUN Local brand assets keep a real transparent background."""

from __future__ import annotations

from pathlib import Path
import struct
import unittest
import zlib


ROOT = Path(__file__).parents[1]
BRAND = ROOT / "custom_components" / "tsun_local" / "brand"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _rgba_pixels(path: Path) -> tuple[int, int, bytes]:
    """Decode an 8-bit, non-interlaced RGBA PNG using only the stdlib."""
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise AssertionError(f"{path} is not a PNG")

    offset = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    idat: list[bytes] = []

    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
        elif chunk_type == b"IDAT":
            idat.append(chunk)
        elif chunk_type == b"IEND":
            break

    if None in (width, height, bit_depth, color_type, interlace):
        raise AssertionError(f"{path} has no valid IHDR")
    if bit_depth != 8 or color_type != 6 or interlace != 0:
        raise AssertionError(
            f"{path} must be 8-bit non-interlaced RGBA; "
            f"got bit_depth={bit_depth}, color_type={color_type}, interlace={interlace}"
        )

    raw = zlib.decompress(b"".join(idat))
    stride = width * 4
    expected = height * (stride + 1)
    if len(raw) != expected:
        raise AssertionError(f"{path} has unexpected decompressed size")

    decoded = bytearray(width * height * 4)
    previous = bytearray(stride)
    source = 0

    def paeth(a: int, b: int, c: int) -> int:
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            return a
        if pb <= pc:
            return b
        return c

    for y in range(height):
        filter_type = raw[source]
        source += 1
        scan = bytearray(raw[source : source + stride])
        source += stride
        for i in range(stride):
            left = scan[i - 4] if i >= 4 else 0
            up = previous[i]
            up_left = previous[i - 4] if i >= 4 else 0
            if filter_type == 0:
                value = scan[i]
            elif filter_type == 1:
                value = (scan[i] + left) & 0xFF
            elif filter_type == 2:
                value = (scan[i] + up) & 0xFF
            elif filter_type == 3:
                value = (scan[i] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                value = (scan[i] + paeth(left, up, up_left)) & 0xFF
            else:
                raise AssertionError(f"{path} uses unsupported PNG filter {filter_type}")
            scan[i] = value
        start = y * stride
        decoded[start : start + stride] = scan
        previous = scan

    return width, height, bytes(decoded)


class BrandTransparencyTests(unittest.TestCase):
    """Protect the transparent TSUN Local artwork in repo, site and HACS source."""

    def test_brand_assets_are_rgba_with_transparent_background(self) -> None:
        for name in ("icon.png", "icon@2x.png", "logo.png", "logo@2x.png"):
            path = BRAND / name
            width, height, rgba = _rgba_pixels(path)
            self.assertEqual(width, height, name)
            alphas = rgba[3::4]
            transparent = sum(alpha == 0 for alpha in alphas)
            opaque = sum(alpha == 255 for alpha in alphas)
            self.assertGreater(transparent, width * height // 20, name)
            self.assertGreater(opaque, width * height // 20, name)
            corners = (
                rgba[3],
                rgba[(width - 1) * 4 + 3],
                rgba[((height - 1) * width) * 4 + 3],
                rgba[((height * width) - 1) * 4 + 3],
            )
            self.assertEqual(corners, (0, 0, 0, 0), name)

            opaque_white = 0
            for index in range(0, len(rgba), 4):
                r, g, b, a = rgba[index : index + 4]
                if a == 255 and r >= 245 and g >= 245 and b >= 245:
                    opaque_white += 1
            self.assertGreater(opaque_white, 10, f"{name}: internal white details lost")

    def test_repo_site_and_hacs_source_use_the_same_artwork(self) -> None:
        self.assertEqual(
            (BRAND / "icon.png").read_bytes(),
            (BRAND / "logo.png").read_bytes(),
        )
        self.assertEqual(
            (BRAND / "icon@2x.png").read_bytes(),
            (BRAND / "logo@2x.png").read_bytes(),
        )
        self.assertEqual(
            (ROOT / "docs" / "icon.png").read_bytes(),
            (BRAND / "icon.png").read_bytes(),
        )

        hacs_workflow = (
            ROOT / ".github" / "workflows" / "publish-hacs-asset.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("source = Path('custom_components/tsun_local')", hacs_workflow)
        self.assertIn("for path in sorted(source.rglob('*'))", hacs_workflow)


if __name__ == "__main__":
    unittest.main()
