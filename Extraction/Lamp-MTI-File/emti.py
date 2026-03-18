import zlib
from dataclasses import dataclass

def c_str(str, color):
    return f'\033[38;5;{color}m{str}\033[0m'

def b_str(bytes, force_hex=False): 
    str = ""
    last_was_hex = False
    color = 48
    for b in bytes:
        # if character is printable ASCII
        if not force_hex and 32 <= b <= 126:
            str += chr(b)
        elif b == 0:
            str += '¦'
        else:
            if last_was_hex:
                color = 196 if color == 48 else 48
            last_was_hex = True

            bs= f'{b:02x}'
            if b == 13:
                bs= '\\r'
            elif b == 10:
                bs= '\\n'

            str += f'\033[38;5;{color}m{bs}\033[0m'
    return str


def open_mti_file(filename):

    # Read MTI file
    with open(filename, "rb") as f:
        data = f.read()

    # Locate zlib stream (usually starts with 0x78)
    zlib_start = data.find(b"\x78")
    if zlib_start == -1:
        raise ValueError("No zlib stream found")

    compressed = data[zlib_start:]
    inflated = zlib.decompress(compressed)

    return inflated


def extract_xml(inflated, end_marker = b'\r\nn\x04\x00p\n\x00\x81\r\nN\x01U\xa9'):
    xml_end = inflated.find(end_marker)
    lines = inflated[:xml_end].split(b'\r\nn"')
    header_xml = "".join([l[2:-1].decode('utf-16le') for l in lines[1:]])

    remainder = inflated[xml_end+14:]
    end_next = b'\r\nP\x01B\x021\x02\x87\r\n'
    end_idx = remainder.find(end_next)
    list = remainder[:end_idx].replace(b'L\r\nn\x10\x02~', b'').replace(b'\xbd\r\nN\x01K', b'').split(b'\r\nn"')
    list_str = "".join([l[2:-1].decode('utf-8') for l in list[1:]])
    return header_xml, list_str


def read_chunk_stream(bytes):
    if len(bytes) == 0:
        return []
    
    size = bytes[0]
    if size == 0:
        return [b""] + read_chunk_stream(bytes[1:])
    elif size > len(bytes)-1:
        return [bytes]
    
    chunk = bytes[1:size+1] 
    return [chunk] + read_chunk_stream(bytes[size+1:])

@dataclass(frozen=True)
class SymbolInfo:
    color: bytes
    label: str
    iconFile: str
    other: str
    message: str

def read_icon_info(c):
    color = b'\xff\xff\xff'
    name = None
    file = None
    other = None
    message = None

    b1 = c[0]
    if b1 == 0x02 or b1 == 10 or b1 == 0x1a:
        color = c[1:4]
        c = c[5:] if b1 == 0x1a else b'\x00' + c[5:]


    if b1 == 0x1a:
        chunks = read_chunk_stream(c)
        if len(chunks) != 3:
            print(f"Unexpected chunk count: {len(chunks)}")
        else:
            name = chunks[0].decode('utf-8', errors='replace').strip()
            file = chunks[1].decode('utf-8', errors='replace')
            other = chunks[2].decode('utf-8', errors='replace')

    elif b1 == 0x18:
        sub_c = read_chunk_stream(c[1:])
        name = sub_c[0].decode('utf-8', errors='replace').strip()
        file = sub_c[1].decode('utf-8', errors='replace')
        if len(sub_c) > 2:
            other = sub_c[2]
        
    elif b1 == 0x19 or (c[0] == 0 and c[1] != 0):
        sub_c = read_chunk_stream(c[1:])
        name = sub_c[0].decode('utf-8', errors='replace').strip()
        file = sub_c[1].decode('utf-8', errors='replace')
        message = sub_c[2];
        message = message.split(b'\xa4')[0].decode('utf-8', errors='replace').strip()

    elif c[:2] == b'\x00\x00':
        size = c[2]
        if size + 3 <= len(c) and size > 0 and size < 32:
            file = c[3:size+3].decode('utf-8', errors='replace')
            name = c[size+3:].decode('utf-8', errors='replace').strip()
    
    return SymbolInfo(color=color, label=name, iconFile=file, other=other, message=message)

def byte2row_col(b):
    row = b >> 4
    col = b & 0x0f
    return [row, col]


M_RECORDS_END_MARKER = b'\r\nN\x08\xddP\x03\r\x08\x11'
M_RECORDS_START_MARKER = b'_MENU404'


# PARSE_MODES = {
#     0x00: "basic", # 0 0 0 0 0 0 0 0
#     0x02: "color", # 0 0 0 0 0 0 1 0
#     0x08: "basic", # 0 0 0 0 0 1 0 0
#     0x0a: "color", # 0 0 0 0 0 1 1 0
#     0x10: "basic", # 0 0 0 0 1 0 0 0
#     0x18: "basic", # 0 0 0 0 1 1 0 0
#     0x19: "basic", # 0 0 0 0 1 1 0 1
#     0x1a: "color", # 0 0 0 0 1 1 1 0
#     0x1b: "color"  # 0 0 0 0 1 1 1 1
# }

class MRecord:
    def __init__(self, m_record, index):
        self.index = index
        self.data = m_record
        chunks = read_chunk_stream(m_record)
        main = chunks[1]
        self.end = chunks[-1]

        
        # Parse the page type and page number
        c1 = chunks[0]
        self.pageType = 0xfd
        if len(c1) == 1:
            self.page = [0,0]
            self.pos = byte2row_col(c1[0])
            self.pageB = b'\x00\x00'
        else:
            b1 = c1[0]
            if b1 == 0xfd:
                self.page = [c1[1], c1[2]]
                self.pageB = c1[1:3]
                self.pos = byte2row_col(c1[3])
            elif b1 == 0xfe:
                self.page = [0,0]
                self.pos = byte2row_col(c1[-1])
            else:
                print(f"records {self.index}: {b_str(c1)}")
                self.pageType = b1
                self.page = [0,0]
                self.pos = [0,0]
                self.header = c1

        self.buttonMode = main[0]
        remainder = main[1:]
        if self.buttonMode & 2 == 0:
            self.parse_basic(remainder)
        else:
            self.parse_color(remainder)

    def parse_3params(self, c):
        chunks = read_chunk_stream(c)
        if len(chunks) == 1:
            print(f"Single chunk in parse_3params ({self.index} ButtonMode={self.buttonMode:02x}): {b_str(c)}")
            return
        
        if len(chunks) < 3:
            print(f"Unexpected chunk count in parse_3params ({self.index} ButtonMode={self.buttonMode:02x}): {b_str(c)}")
            chunks.append(b"") # pad to avoid index error, but likely missing info 
        
        self.label = chunks[0]
        self.iconName = chunks[1]
        self.message = chunks[2]

    def parse_basic(self, c):
        self.color = [0xff, 0xff, 0xff]
        self.parse_3params(c)

    def parse_color(self, c):
        self.color = c[:3]
        self.parse_3params(c[4:])


    def __str__(self):

        pos_str = f"{self.pos[0]}, {self.pos[1]}"

        page_num = self.page[0] * 9 + self.page[1]
        page_str = f"Page({page_num}) Cell({pos_str})" if self.pageType == 0xfd else f"PageType({self.pageType})"
    
        
        label_str = f"Label({b_str(self.label)})" if len(self.label) > 0 else ""
        icon_str = f"Icon({b_str(self.iconName)})" if len(self.iconName) > 0 else ""
        message_str = f"Message({b_str(self.message)})" if len(self.message) > 0 else ""
        btn_mode = f"ButtonMode({b_str([self.buttonMode])})"
        info_str = " ".join([s for s in [btn_mode, label_str, icon_str, message_str] if s])
     
        return f"record: {self.index} {page_str} {info_str}"   

    def to_dict(self):
        res = {
            "index": self.index,
            "pageType": self.pageType,
            "page": self.page,
            "pos": self.pos,
            "buttonMode": self.buttonMode,
            "color": [self.color[0], self.color[1], self.color[2]],
            "label": self.label.decode('utf-8', errors='replace'),
            "iconName": self.iconName.decode('utf-8', errors='replace'),
            "message": self.message.decode('utf-8', errors='replace'),
        }
        return res

def parse_mti_m_records(filename):
    data = open_mti_file(filename)

    m_records_start = data.find(M_RECORDS_START_MARKER)
    m_records_end = data.find(M_RECORDS_END_MARKER)

    m_record_lines = data[m_records_start:m_records_end].split(b'\r\nm\x00')[1:]

    m_records = [MRecord(l.split(b'\r\nx\x00')[0], i) for i, l in enumerate(m_record_lines)]
    
    return m_records

m_records = parse_mti_m_records("lamp.mti")

import json
with open("m_records.json", "w") as f:
    json.dump([m.to_dict() for m in m_records], f, indent=2) 
