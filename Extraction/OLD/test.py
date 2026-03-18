
from pathlib import Path

def print_tree(root=".", max_depth=None, show_hidden=False):
    root = Path(root)
    base_depth = len(root.resolve().parts)

    for p in sorted(root.rglob("*")):
        if not show_hidden and any(part.startswith(".") for part in p.relative_to(root).parts):
            continue
            
        #skip wav files
        if p.suffix.lower() == ".wav":
            continue
        
        depth = len(p.resolve().parts) - base_depth
        if max_depth is not None and depth > max_depth:
            continue

        indent = "  " * depth
        suffix = "/" if p.is_dir() else ""
        print(f"{indent}{p.name}{suffix}")

import os


import zlib, hashlib
RID2 = "3331CD2D-F450D447-B95AD294-9364F663"
RID = "728565A6B3F95B48BEB9BFBD37F4AD22"
# RID = "728565A6-B3F95B48-BEB9BFBD-37F4AD22"
rid = RID.encode()

# 1921344934,3019463496,3199844285,938781986
print(bytes.fromhex(RID))
formats = [
    hex(zlib.crc32(rid)),
    hashlib.md5(rid).hexdigest(),
    hashlib.sha1(rid).hexdigest(),
    RID.encode("ascii"),
    RID.encode("utf-16le"),
    RID.encode("utf-16be"),
    bytes.fromhex(RID),
    bytes.fromhex(RID[::-1])
]
root = "./NuVoiceAPp/data"
for dirpath, _, filenames in os.walk(root):
    for name in filenames:
        path = os.path.join(dirpath, name)
        try:
            data = open(path, "rb").read()
        except:
            continue

        for fmt in formats:
            if isinstance(fmt, str):
                fmt = fmt.encode()

            if fmt in data:
                print(f"Found {fmt} in {path}")
            # else:
            #     print(".", end="")
   
       
# print_tree("./NuVoiceAPp/commonappdata", max_depth=None, show_hidden=True)