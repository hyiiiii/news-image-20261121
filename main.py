#!/usr/bin/env python3
"""Dependency-free installer for the shipped make.fun entry image."""

from __future__ import annotations

import binascii
import os
import struct
import sys
import zlib
from pathlib import Path

MAX_BYTES = 1_048_576
WIDTH = 1024
HEIGHT = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ASSET_PATH = Path(__file__).resolve().parent / "assets" / "entry.png"
OUTPUT_PATH = Path("/output/entry.png")


class EntryValidationError(ValueError):
    pass


def _read_png_payload(data: bytes) -> tuple[int, int, list[bytes]]:
    if not data.startswith(PNG_SIGNATURE):
        raise EntryValidationError("asset is not a PNG file (bad signature)")

    position = len(PNG_SIGNATURE)
    first = True
    width = height = 0
    idat_parts: list[bytes] = []
    seen_iend = False

    while position < len(data):
        if position + 12 > len(data):
            raise EntryValidationError("truncated PNG chunk header")
        length = struct.unpack(">I", data[position:position + 4])[0]
        chunk_type = data[position + 4:position + 8]
        data_start = position + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(data):
            raise EntryValidationError("truncated PNG chunk body")
        chunk_data = data[data_start:data_end]
        expected_crc = struct.unpack(">I", data[data_end:crc_end])[0]
        actual_crc = binascii.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise EntryValidationError(f"bad CRC in {chunk_type!r} chunk")

        if first:
            if chunk_type != b"IHDR":
                raise EntryValidationError("IHDR must be the first PNG chunk")
            first = False
            if length != 13:
                raise EntryValidationError("IHDR has an invalid length")
            (width, height, bit_depth, color_type, compression,
             filter_method, interlace) = struct.unpack(">IIBBBBB", chunk_data)
            if (width, height) != (WIDTH, HEIGHT):
                raise EntryValidationError(
                    f"asset must be {WIDTH}x{HEIGHT}, got {width}x{height}"
                )
            if bit_depth != 8 or color_type != 2:
                raise EntryValidationError("asset must be 8-bit RGB truecolor")
            if compression != 0 or filter_method != 0 or interlace != 0:
                raise EntryValidationError("unsupported PNG compression, filter, or interlace")
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            if length != 0:
                raise EntryValidationError("IEND chunk must be empty")
            seen_iend = True
            position = crc_end
            if position != len(data):
                raise EntryValidationError("unexpected bytes after IEND")
            break

        position = crc_end

    if not seen_iend:
        raise EntryValidationError("PNG has no IEND chunk")
    if not idat_parts:
        raise EntryValidationError("PNG has no image data")
    return width, height, idat_parts


def validate_png(data: bytes) -> tuple[int, int]:
    if not data:
        raise EntryValidationError("asset is empty")
    if len(data) > MAX_BYTES:
        raise EntryValidationError(
            f"asset exceeds {MAX_BYTES} bytes (got {len(data)})"
        )
    width, height, idat_parts = _read_png_payload(data)

    try:
        raw = zlib.decompress(b"".join(idat_parts))
    except zlib.error as exc:
        raise EntryValidationError(f"invalid compressed image data: {exc}") from exc

    row_bytes = 1 + width * 3
    expected = height * row_bytes
    if len(raw) != expected:
        raise EntryValidationError(
            f"unexpected scanline data length ({len(raw)} != {expected})"
        )
    for row in range(height):
        filter_type = raw[row * row_bytes]
        if filter_type > 4:
            raise EntryValidationError(f"invalid PNG filter type {filter_type} in row {row}")
    return width, height


def install(asset_path: Path = ASSET_PATH, output_path: Path = OUTPUT_PATH) -> int:
    try:
        data = asset_path.read_bytes()
    except OSError as exc:
        raise EntryValidationError(f"cannot read asset {asset_path}: {exc}") from exc

    validate_png(data)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output_path.with_name(output_path.name + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, output_path)
    except OSError as exc:
        raise EntryValidationError(f"cannot write {output_path}: {exc}") from exc
    return len(data)


def main() -> int:
    try:
        written = install()
    except EntryValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {OUTPUT_PATH} ({WIDTH}x{HEIGHT}, {written} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
