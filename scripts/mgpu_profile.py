#!/usr/bin/env python3
"""Apply a documented bridge preset, preserving unrelated INI settings."""
import argparse
import os
from pathlib import Path
import re
import stat
import tempfile


PROFILES = {
    "native": {"SRUpscale": "0", "SRScale": "0", "SRMvLowRes": "0"},
    "native-upscale": {"SRUpscale": "1", "SRScale": "0", "SRMvLowRes": "0"},
}
# One neural evaluation per frame; retain coherent ring transport and disable
# diagnostic work. Do not change artistic intensity, device/monitor or AutoArm.
COMMON = {"Passes": "1", "RingWindow": "1", "Stride": "0",
          "MetaProbe": "off", "MVecProbe": "0", "DepthCompare": "0",
          "Probes": "0", "Profile": "0"}


def render(raw: bytes, profile: str) -> bytes:
    text = raw.decode("utf-8-sig")
    if "\x00" in text:
        raise ValueError("NUL in INI; refusing unsupported encoding")
    settings = COMMON | PROFILES[profile]
    lines = text.splitlines(keepends=True)
    sections = [(i, m.group(1).strip().lower()) for i, line in enumerate(lines)
                if (m := re.match(r"^\s*\[([^]]+)\]\s*(?:[;#].*)?$", line.strip()))]
    starts = [i for i, section in sections if section == "mgpu"]
    if len(starts) != 1:
        raise ValueError("Expected exactly one [MGPU] section")
    start = starts[0]
    end = next((i for i, _ in sections if i > start), len(lines))
    newline = "\r\n" if "\r\n" in text else "\n"
    found = set()
    lookup = {key.lower(): key for key in settings}
    for i in range(start + 1, end):
        match = re.match(r"^(\s*)([^=;#]+?)(\s*=\s*)([^;#\r\n]*)(.*)$",
                         lines[i].rstrip("\r\n"))
        if not match or match[2].strip().lower() not in lookup:
            continue
        key = lookup[match[2].strip().lower()]
        if key in found:
            raise ValueError(f"Duplicate MGPU setting: {key}")
        found.add(key)
        lines[i] = f"{match[1]}{match[2]}{match[3]}{settings[key]}{match[5]}{newline}"
    if end and not lines[end - 1].endswith(("\n", "\r")):
        lines[end - 1] += newline
    lines[end:end] = [f"{key}={value}{newline}" for key, value in settings.items()
                      if key not in found]
    return (b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + "".join(lines).encode()


def apply(path: Path, profile: str, preview: bool) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError("INI must be an existing regular file, not a symlink")
    raw = path.read_bytes()
    updated = render(raw, profile)
    print(f"MGPU profile: {profile} ({path})")
    for key, value in (COMMON | PROFILES[profile]).items():
        print(f"  {key}={value}")
    if preview or updated == raw:
        print("Preview only" if preview else "Already configured")
        return
    # Back up exact bytes for each actual change; never overwrite a prior backup.
    fd, backup = tempfile.mkstemp(prefix=path.name + ".backup-", dir=path.parent)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    fd, staging = tempfile.mkstemp(prefix=".mgpu-profile-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(staging, stat.S_IMODE(path.stat().st_mode))
        if path.read_bytes() != raw:
            raise ValueError("INI changed concurrently; refusing to replace it")
        os.replace(staging, path)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)
    print(f"Backup: {backup}")
    print("Restore this backup with the game closed to undo the preset.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ini", type=Path, required=True)
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    try:
        apply(args.ini, args.profile, args.preview)
    except (OSError, ValueError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
