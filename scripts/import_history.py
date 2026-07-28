from __future__ import annotations

import base64
import io
import lzma
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def is_safe_member(member: tarfile.TarInfo) -> bool:
    target = (ROOT / member.name).resolve()
    return target == ROOT or ROOT in target.parents


def main() -> None:
    parts = sorted(DATA_DIR.glob("history.part*.b64"))
    if not parts:
        raise RuntimeError("No historical archive parts were found")

    encoded = "".join(
        part.read_text(encoding="ascii").strip() for part in parts
    )
    compressed = base64.b64decode(encoded, validate=True)
    archive = lzma.decompress(compressed)

    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        members = bundle.getmembers()
        unsafe = [member.name for member in members if not is_safe_member(member)]
        if unsafe:
            raise RuntimeError(f"Unsafe archive paths: {unsafe}")
        bundle.extractall(ROOT, members=members, filter="data")

    posts = sorted((ROOT / "_posts").glob("*.md"))
    if len(posts) != 19:
        raise RuntimeError(f"Expected 19 historical posts, generated {len(posts)}")

    print(f"Generated {len(posts)} historical Jekyll posts")


if __name__ == "__main__":
    main()
