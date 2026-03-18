from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass
from pathlib import Path


RID_8x4_RE = re.compile(r'"rid"\s*:\s*"\{([0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{8}){3})\}"')


def read_rids_from_test_json(path: Path) -> set[str]:
    rids: set[str] = set()
    with path.open('r', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = RID_8x4_RE.search(line)
            if m:
                rids.add(m.group(1).upper())
    return rids


def icon_names_from_extracted(root: Path) -> set[str]:
    names: set[str] = set()
    for p in root.rglob('*.png'):
        names.add(p.stem)
    return names


def fmt_8x4_hex(raw16: bytes) -> str:
    h = raw16.hex().upper()
    return f"{h[:8]}-{h[8:16]}-{h[16:24]}-{h[24:32]}"


def fmt_8x4_hex_dword_le(raw16: bytes) -> str:
    # reverse bytes within each 32-bit word
    chunks = [raw16[i : i + 4][::-1].hex().upper() for i in range(0, 16, 4)]
    return "-".join(chunks)


def candidate_payloads(name: str) -> list[bytes]:
    payloads: list[bytes] = []
    for s in (name, name.lower(), name.upper()):
        payloads.append(s.encode('utf-8'))
        payloads.append((s + "\x00").encode('utf-8'))
        payloads.append(s.encode('utf-16le'))
        payloads.append((s + "\x00").encode('utf-16le'))
    # de-dup while preserving order
    seen: set[bytes] = set()
    out: list[bytes] = []
    for p in payloads:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


@dataclass(frozen=True)
class Match:
    rid: str
    icon_name: str
    rule: str


def main() -> None:
    repo_root = Path(__file__).resolve().parent

    test_json = repo_root / 'test.json'
    icons_root = repo_root / 'NuVoiceAPp' / 'IconsExtracted'

    if not test_json.exists():
        raise SystemExit(f"Missing {test_json}")
    if not icons_root.exists():
        raise SystemExit(f"Missing {icons_root}")

    rids = read_rids_from_test_json(test_json)
    icons = icon_names_from_extracted(icons_root)

    print(f"Loaded RIDs from test.json: {len(rids)}")
    print(f"Loaded extracted icon names: {len(icons)}")

    # Try to match RID == hash(icon_name) under a few plausible formatting / encoding rules
    found: dict[str, Match] = {}

    for icon in icons:
        for payload in candidate_payloads(icon):
            md5 = hashlib.md5(payload).digest()

            rid_a = fmt_8x4_hex(md5)
            if rid_a in rids and rid_a not in found:
                found[rid_a] = Match(rid=rid_a, icon_name=icon, rule='md5(payload) hex 8-8-8-8')

            rid_b = fmt_8x4_hex_dword_le(md5)
            if rid_b in rids and rid_b not in found:
                found[rid_b] = Match(rid=rid_b, icon_name=icon, rule='md5(payload) dword-le 8-8-8-8')

            rid_c = fmt_8x4_hex(md5[::-1])
            if rid_c in rids and rid_c not in found:
                found[rid_c] = Match(rid=rid_c, icon_name=icon, rule='md5(payload) reversed bytes')

    print(f"Matches found: {len(found)}")

    # Print a stable sample
    for rid in sorted(list(found.keys()))[:50]:
        m = found[rid]
        print(f"{m.rid} -> {m.icon_name} ({m.rule})")

    # Highlight your example RIDs if present
    examples = [
        '728565A6-B3F95B48-BEB9BFBD-37F4AD22',
        '3331CD2D-F450D447-B95AD294-9364F663',
    ]
    for ex in examples:
        m = found.get(ex)
        if m:
            print(f"EXAMPLE {ex} -> {m.icon_name} ({m.rule})")
        else:
            print(f"EXAMPLE {ex} -> (no match)")


if __name__ == '__main__':
    main()
