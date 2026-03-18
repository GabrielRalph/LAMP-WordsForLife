

# data = open("NuVoiceAPp/app/PRCBuildIconData.dll", "rb").read()
import pefile
import struct

# {9D72D5D0-344CF64B-8EA293A4-868EA9D9}
# {98E7E963-3F554445-AB694ED1-F61D6281}
pe = pefile.PE("NuVoiceAPp/app/PRCBuildIconData.dll")
def rva_to_section(rva):
    for s in pe.sections:
        start = s.VirtualAddress
        end = start + s.Misc_VirtualSize
        if start <= rva < end:
            return s
    return None

def is_rva_in_text(rva):
    s = rva_to_section(rva)
    return s and s.Name.startswith(b".text")

def find_pointer_tables(min_len=3):
    results = []

    for s in pe.sections:
        if not s.Name.startswith(b".rdata"):
            continue

        data = s.get_data()
        base_rva = s.VirtualAddress

        i = 0
        while i <= len(data) - 4:
            table = []
            j = i

            while j <= len(data) - 4:
                val, = struct.unpack_from("<I", data, j)
                if is_rva_in_text(val):
                    table.append(val)
                    j += 4
                else:
                    break

            if len(table) >= min_len:
                results.append({
                    "rva": base_rva + i,
                    "count": len(table),
                    "type": "pointer_table"
                })
                i = j
            else:
                i += 4

    return results


def find_int_tables(min_len=8):
    results = []

    for s in pe.sections:
        if not s.Name.startswith((b".rdata", b".data")):
            continue

        data = s.get_data()
        base_rva = s.VirtualAddress

        i = 0
        while i <= len(data) - 4:
            table = []
            j = i

            while j <= len(data) - 4:
                val, = struct.unpack_from("<I", data, j)
                if val < 0x10000:  # heuristic: small ints
                    table.append(val)
                    j += 4
                else:
                    break

            if len(table) >= min_len:
                results.append({
                    "rva": base_rva + i,
                    "count": len(table),
                    "type": "int_table"
                })
                i = j
            else:
                i += 4

    return results


def find_byte_tables(min_len=32):
    results = []

    for s in pe.sections:
        if not s.Name.startswith(b".rdata"):
            continue

        data = s.get_data()
        base_rva = s.VirtualAddress

        i = 0
        while i < len(data):
            j = i
            while j < len(data) and data[j] not in (0x00,):
                j += 1

            if j - i >= min_len:
                results.append({
                    "rva": base_rva + i,
                    "count": j - i,
                    "type": "byte_table"
                })

            i = j + 1

    return results


ptrs = find_pointer_tables()
ints = find_int_tables()
bytes_ = find_byte_tables()

print("\n[ Pointer tables ]")
for r in ptrs:
    print(f"RVA=0x{r['rva']:08X}  entries={r['count']}")

print("\n[ Integer tables ]")
for r in ints:
    print(f"RVA=0x{r['rva']:08X}  entries={r['count']}")

print("\n[ Byte tables ]")
for r in bytes_:
    print(f"RVA=0x{r['rva']:08X}  bytes={r['count']}")
