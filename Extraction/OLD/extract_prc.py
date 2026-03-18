import os

def b_str(bytes): 
    str = ""
    for b in bytes:
        # if character is printable ASCII
        if 32 <= b <= 126:
            str += chr(b)
        elif b == 0:
            str += '¦'
        else:
            str += '†'
    return str


def extract_prc(data):
    # initial header size
    b = int.from_bytes(data[4:8], "little")    
    header_size = int.from_bytes(data[8:12], "little")     # 0x2E358 = 189272

    # number of entries
    n_e = (header_size - b) // 18

    # entry header bytes
    entry_headers_b = data[b:header_size]

    # entry data bytes
    entry_data_b = data[header_size:]
    
    # for each entry 
    entries = []
    for i in range(n_e):
        # entry info seems to have 18 byte structure
        # 8 bytes: name (chars)
        # 2 bytes: unknown probably padding
        # 4 bytes: offset (little-endian int)
        # 4 bytes: size (little-endian int)

        # get entry bytes
        entry = entry_headers_b[i*18:(i+1)*18]

        # name stored in first 8 bytes
        name = entry[0:8].replace(b'\x00', b'').decode('latin-1', errors='replace')
       
        offset = int.from_bytes(entry[-8:-4], "little")
        size = int.from_bytes(entry[-4:], "little")
        entries.append({
            "entry_desc": b_str(entry),
            "name": name,
            "offset": offset,
            "size": size,
            "data": entry_data_b[offset:(offset+size)],
        })
    return entries

def get_symbols(root_dir, save_dir):
    # get all files that end with .prc
    prc_files = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".prc"):
                prc_files.append(os.path.join(subdir, file))

    
    for prc_file in prc_files:
        data = open(prc_file, "rb").read()
        entries = extract_prc(data)
        for entry in entries:
            name = entry["name"]
            edata = entry["data"]
            len(edata)
            with open(os.path.join(save_dir, f"{name}.png"), "wb") as f:
                f.write(edata)

def get_all_icons(root_dir, save_dir): 
    # get all sub directories in the root directory
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

    # create save directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # create sub directories in the save directory
    for subdir in subdirs:
        if not os.path.exists(os.path.join(save_dir, subdir)):
            os.makedirs(os.path.join(save_dir, subdir)) 

    for subdir in subdirs:
        get_symbols(os.path.join(root_dir, subdir), os.path.join(save_dir, subdir))


get_all_icons("commonappdata/cm$MyCompanyName/code$MyGetUserAppName/Icons", "IconsExtracted")