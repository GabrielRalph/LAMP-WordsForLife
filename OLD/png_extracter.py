
PNG_SIG = b"\x89PNG\r\n\x1a\n"
CHUNK_TYPES = set([
    b"IHDR",
    b"PLTE",
    b"IDAT",
    b"bKGD",
    b"cHRM",
    b"cICP",
    b"dSIG",
    b"eXIf",
    b"gAMA",
    b"hIST",
    b"iCCP",
    b"iTXt",
    b"pHYs",
    b"sBIT",
    b"sPLT",
    b"sRGB",
    b"sTER",
    b"tEXt",
    b"tIME",
    b"tRNS",
    b"zTXt"
])
END_CHUNK_TYPE = b"IEND"

chunk_logs = set()
def extract_png(blob: bytes, offset: int) -> None | bytes:
    """Return the full PNG bytes starting at offset, or None if invalid."""
    n = len(blob)

    # Check offset is in valid range
    if offset > 0 and offset + 8 < n:

        # Check for PNG signature
        if blob[offset : offset + 8] == PNG_SIG:
            i = offset + 8

            # Scan forward for the chunks in the PNG
            while i + 12 <= n:
                chunk_len = int.from_bytes(blob[i : i + 4], "big")
                chunk_type = blob[i + 4 : i + 8]
                if chunk_type == END_CHUNK_TYPE:
                    return blob[offset:i + 12]
                elif chunk_type not in CHUNK_TYPES:
                    print(f"Unknown chunk type {chunk_type} at offset {i}")
                    return None
                else:
                    chunk_logs.add(chunk_type)
                    i = i + 12 + chunk_len

            print("Reached end of blob without finding IEND chunk")

            
    return None

def is_png(blob: bytes, offset: int) -> bool:
    n = len(blob)
    return offset > 0 and offset + 8 < n and blob[offset : offset + 8] == PNG_SIG