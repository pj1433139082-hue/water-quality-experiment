"""Read-only skill resource identity check.

This script reads the resource manifest embedded at the end of this skill's
``SKILL.md`` and verifies that every listed file still has its exact recorded
byte length and SHA-256. It is deliberately standalone: it imports no project
module, opens no network connection, and writes nothing.

Contract:

* a listed file that is missing, redirected, or whose bytes/digest drifted is a
  ``HOLD`` -- the caller must stop any action that depends on that resource;
* a resource file present on disk but absent from the manifest is also a
  ``HOLD``: adding or changing a resource without updating the manifest would
  otherwise leave the manifest quietly incomplete;
* the check proves manifest identity only. It is not a proof of a complete
  protocol closure, and it is not a same-handle guarantee against an
  adversarial process that rewrites a file between the check and its use.

Exit codes: ``0`` for PASS, ``2`` for HOLD.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import hashlib
import json
import re
from pathlib import Path

MANIFEST_SCHEMA = "water-quality-skill-resources-v1"
MANIFEST_PATTERN = re.compile(
    r"<!--\s*" + re.escape(MANIFEST_SCHEMA) + r"\s*(?P<body>\{.*?\})\s*-->",
    re.DOTALL,
)
SCANNED_SUFFIXES = {"references": ".md", "scripts": ".py"}


class ResourceError(RuntimeError):
    """Carries a stable machine-readable ``code`` in the message and attribute."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def _read_manifest(skill_md: Path) -> list[dict]:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        raise ResourceError("SKILL_MANIFEST_UNREADABLE", str(exc)) from exc
    match = MANIFEST_PATTERN.search(text)
    if match is None:
        raise ResourceError("SKILL_MANIFEST_MISSING")
    try:
        manifest = json.loads(match.group("body"))
    except ValueError as exc:
        raise ResourceError("SKILL_MANIFEST_INVALID_JSON", str(exc)) from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA:
        raise ResourceError("SKILL_MANIFEST_SCHEMA_MISMATCH")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ResourceError("SKILL_MANIFEST_HAS_NO_FILES")
    return files


def _resolve_within(skill_root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ResourceError("SKILL_RESOURCE_PATH_INVALID", repr(relative))
    candidate = Path(relative)
    if candidate.is_absolute() or candidate.drive or ".." in candidate.parts:
        raise ResourceError("SKILL_RESOURCE_PATH_ESCAPES_SKILL", relative)
    resolved = (skill_root / candidate).resolve(strict=False)
    if resolved != skill_root and skill_root not in resolved.parents:
        raise ResourceError("SKILL_RESOURCE_PATH_ESCAPES_SKILL", relative)
    if resolved.is_symlink() or (skill_root / candidate).is_symlink():
        raise ResourceError("SKILL_RESOURCE_REDIRECTED", relative)
    return resolved


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _verify(skill_root: Path, entries: list[dict]) -> dict[str, bytes]:
    resources: dict[str, bytes] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ResourceError("SKILL_MANIFEST_ENTRY_INVALID", repr(entry))
        relative = entry.get("path")
        path = _resolve_within(skill_root, relative)
        if not path.is_file():
            raise ResourceError("SKILL_RESOURCE_MISSING", str(relative))
        raw = path.read_bytes()
        if not isinstance(entry.get("bytes"), int) or entry["bytes"] != len(raw):
            raise ResourceError(
                "SKILL_RESOURCE_BYTES_MISMATCH",
                f"{relative} declared={entry.get('bytes')} actual={len(raw)}",
            )
        actual = _digest(raw)
        if not isinstance(entry.get("sha256"), str) or entry["sha256"] != actual:
            raise ResourceError(
                "SKILL_RESOURCE_SHA256_MISMATCH",
                f"{relative} declared={entry.get('sha256')} actual={actual}",
            )
        resources[str(relative).replace("\\", "/")] = raw
    return resources


def _unlisted(skill_root: Path, resources: dict[str, bytes]) -> list[str]:
    listed = set(resources)
    found: list[str] = []
    for folder, suffix in SCANNED_SUFFIXES.items():
        directory = skill_root / folder
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.suffix != suffix:
                continue
            relative = f"{folder}/{path.name}"
            if relative not in listed:
                found.append(relative)
    return found


def main() -> int:
    skill_root = Path(__file__).absolute().parent.parent
    try:
        entries = _read_manifest(skill_root / "SKILL.md")
        resources = _verify(skill_root, entries)
        unlisted = _unlisted(skill_root, resources)
        if unlisted:
            raise ResourceError("SKILL_RESOURCE_UNLISTED", ",".join(unlisted))
    except ResourceError as exc:
        result = {
            "status": "HOLD",
            "reason": exc.code,
            "detail": str(exc),
            "mutations_performed": False,
        }
        code = 2
    except (OSError, ValueError) as exc:
        result = {
            "status": "HOLD",
            "reason": type(exc).__name__,
            "detail": str(exc),
            "mutations_performed": False,
        }
        code = 2
    else:
        result = {
            "status": "PASS",
            "resources": sorted(resources),
            "resource_bytes": sum(len(raw) for raw in resources.values()),
            "scope": "read_only_manifest_identity_not_native_closure",
            "mutations_performed": False,
        }
        code = 0
    print(json.dumps(result, ensure_ascii=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
