import json

# read json
pages = {}
with open("pages.json", "r") as f:
    pages = json.load(f)


icon_map = {}
with open("MTI/mti_extracted.json", "r") as f:
    mti = json.load(f)
    icon_map = mti.get("icon_map", {})


print(f"Total icons in icon_map: {len(icon_map)}")

backspace_prc = "BACKSPA-"
backspace_scsh = "DELCHAR"
rid_2_icons = {
    "{05B5D762-86D8884E-B03CE6E1-49B3435E}": set(["GOBACKLF"]),
    "{CAF8EEF4-BAF64A85-8C0F246C-E5C10075}": set([backspace_prc])
}
button_status = {}
button_by_id = {}



no_match_set = set()
no_match_rid = set()
multi_match = set()

for page_num, page in pages.items():
    buttons = page.get("buttons", [])
    for bi, button in enumerate(buttons):
        button_id = str(page_num) + "-" + str(bi)
        button_by_id[button_id] = button

        name = button.get("message", button.get("label", None))
        rid = button.get("symbol_link", {}).get("rid", None)
        if rid and name:
                name = name.strip()
                icon = icon_map.get(name, None)
                if icon:
                    button["icon_file"] = icon
                    button_status[button_id] = 1
                    if not rid in rid_2_icons:
                        rid_2_icons[rid] = set()
                    rid_2_icons[rid].add(icon)
                else:
                    name_caps = name.upper()[:7]
                    file_name = "./NuVoiceAPp/IconsExtracted/SCSH/" + name_caps + ".png"
                    # check file exists
                    try:
                        with open(file_name, "rb") as f:
                            button["icon_file"] = name_caps
                            button_status[button_id] = 1
                            if not rid in rid_2_icons:
                                rid_2_icons[rid] = set()
                            rid_2_icons[rid].add(name_caps)
                    except FileNotFoundError:
                        a = 0
            
matched = sum(v for _, v in button_status.items())  
total = len(button_by_id)  
print(f"First pass: total buttons: {total}, matched icons: {matched}, missing: {total - matched}")

for button_id, button in button_by_id.items():
    status = button_status.get(button_id, 0)
    if status == 0:
        rid = button.get("symbol_link", {}).get("rid", None)
        if rid and rid in rid_2_icons:
            icons = rid_2_icons.get(rid, None)
            if icons:
                icon = list(icons)[0]
                button["icon_file"] = icon
                button_status[button_id] = 1
                if len(icons) > 1:
                    button_status[button_id] = 2
   
matched = sum(1 if v > 0 else 0 for _, v in button_status.items())
total = len(button_by_id)  
print(f"Second pass: total buttons: {total}, matched icons: {matched}, missing: {total - matched}")

missing_names = set()
missing_rids = set()
for button_id, button in button_by_id.items():
    status = button_status.get(button_id, 0)
    if status == 0:
        name = button.get("message", button.get("label", None))
        if name:
            name = name.strip()
            missing_names.add(name)
        else:
            rid = button.get("symbol_link", {}).get("rid", None)
            if rid:
                missing_rids.add(rid)

miss_names_list = "\n\t- ".join([n for n in missing_names]);
miss_rids_list = "\n\t- ".join([r for r in missing_rids]);
print(f"Missing names\n\t{miss_names_list}\nMissing RIDS:\n\t{miss_rids_list}")
   
with open("pages_with_icons.json", "w") as f:
    json.dump(pages, f, indent=2)   

