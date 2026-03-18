# finished = 73339DEE-730847F9-8AD58BBB-0EE4D2FE

# perform a shar256 hash on a file and return the hex digest
import hashlib
from pathlib import Path

def fmt_8_8_8_8(hex32: str) -> str:
    h = hex32.upper()
    return f"{h[0:8]}-{h[8:16]}-{h[16:24]}-{h[24:32]}"

def md5_rid(data: bytes) -> str:
    return fmt_8_8_8_8(hashlib.md5(data).hexdigest())

def md5_rid_of_name(path: Path) -> str:
    # In case the RID is based on the icon key/name rather than the bytes
    name = path.stem  # filename without .png
    return fmt_8_8_8_8(hashlib.md5(name.encode("utf-8", errors="replace")).hexdigest())


def main():
    target = "1DB3C903-81C9DD48-90C482ED-18C073B7".upper()
    root = Path("NuVoiceAPp/IconsExtracted")

    hits = []
    for p in root.rglob("*.png"):
        b = p.read_bytes()

        if md5_rid(b) == target:
            hits.append(("md5(bytes)", p))
            print(".")


        if md5_rid_of_name(p) == target:
            hits.append(("md5(name)", p))
            print(".")

    if not hits:
        print("No matches.")
        return

    for kind, p in hits:
        print(f"MATCH [{kind}]: {p}")

if __name__ == "__main__":
    main()