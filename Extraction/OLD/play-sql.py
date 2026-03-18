import sqlite3
conn = sqlite3.connect('lamp_ce/lamp.sqlite')
cursor = conn.cursor()




ACTION_CODES = {
    # {65, 4, 6, 7, 8, 39, 10, 40, 41, 42, 43, 73, 16, 74, 20, 28, 29, 30}
    '65': 'add an s if possible',
    '4': 'play audio file',
    '6': 'Go back',
    '7': 'Go back (ok)',
    '8': 'Goto page stop go to home for 10',
    '39': 'placeholder',
    '10': 'Add word and go to home',
    '40': 'Volume up',
    '41': 'Volume down',
    '42': 'adds phonics',
    '43': 'Delete currently typed word',
    '73': 'Goto to page',
    '16': 'Backspace',
    '74': 'Open Word finder',
    '20': 'speaks everythin',
    '28': 'Clear everything',
    '29': 'speaks last word',
    '30': '',
}
BUTTON_DEFAULTS = {
    'message': '',
    'label': '',
    'visible': 1,
    'pronunciation': None,
    'skin_tone_override': None,
    'symbol_link': None,
    'position': None,
    'span': (1, 1),
    'style': {},
    'actions': [],
}
BUTTON_STYLE_DEFAULTS = {
    'label_on_top': 1,
    'body_color': 16777215,
    'border_width': 2,
    'font_bold': 0,
    'font_height': 10,
}
ACTION_DEFAULTS = {
    'rank': None,
    'code': None,
    'data': [],
}
ACTION_DATA_DEFAULTS = {
    'key': None,
    'value': None,
}

def parse_obj(obj, props):
    styles = {}
    for k, v in props.items():
        if obj[k] != v:
            styles[k] = obj[k]
    return styles

def is_unique():
    title = cursor.description[0][0]
    ids = [r[0] for r in cursor.fetchall()]
    unique_ids = set(ids)
    if len(ids) != len(unique_ids):
        print(f"Found {len(ids) - len(unique_ids)} duplicate {title} values")
    else:
        print(f"All {title} values are unique")

cursor.execute('SELECT page_id, id FROM button_box_instances')
a = cursor.fetchall()
d = [p1 - p2 for p1, p2 in a]
print(d)

def get_object():
    res = []
    for value in cursor.fetchall():
        r = {}
        for idx, col in enumerate(cursor.description):
            r[col[0]] = value[idx]
        res.append(r)

    return res

def get_pages_by_resource(resource_id):
    cursor.execute(f'SELECT * FROM pages WHERE resource_id={resource_id}')
    pages = get_object()
    return pages

def get_resource_by_value(value):
    cursor.execute(f'SELECT * FROM resources WHERE rid="{value}"')
    resources = get_object()
    return resources


class ActionData:
    def __init__(self, data):
        self.key = data.get('key', None)
        self.value = data.get('value', "")
        rids = get_resource_by_value(self.value)
        self.resource = None
        self.page_id = None
        if len(rids) > 0:
            self.resource = rids[0]
            pages = get_pages_by_resource(self.resource['id'])
            if len(pages) > 0:
                self.page_id = pages[0]['id']

    def __str__(self):
        if self.page_id is not None:
            return f"Linked Page: {self.page_id}"
        elif self.resource is not None:
            return f"Linked Resource: {self.resource['rid']}"
        else:
            return f"Value: {self.value}"

class Action:
    def __init__(self, action):
        self.rank = action.get('rank', None)
        self.code = action.get('code', None)
        self.id = action.get('id', None)
        cursor.execute(f'SELECT * FROM action_data WHERE action_id={self.id}')
        self.data = [ActionData(d) for d in get_object()]
        
    @property
    def linked_page(self):
        for d in self.data:
            if d.page_id is not None:
                return d.page_id
        return None
    
    def __str__(self):
        if self.code == 73:
            return f"C{self.code} R{self.rank} Page: {self.linked_page}"
        else:
            data = ",".join([str(a) for a in self.data])
            return f"C{self.code} R{self.rank} {data}"


class Actions:
    def __init__(self, resource_id):
        cursor.execute(f'SELECT * FROM actions WHERE resource_id={resource_id}')
        self.list = [Action(o) for o in get_object()]
    
    def get_linked_page(self):
        for action in self.list:
            page_id = action.linked_page
            if page_id is not None:
                return page_id
        return None
    
    def __str__(self):
        return " | ".join([str(a) for a in self.list])
    

def print_object(obj, d = 1):
    for k, v in obj.items():
        if isinstance(v, list):
            _v = {}
            for i, item in enumerate(v):
                _v[f'[{i}]'] = item
            v = _v

        if isinstance(v, dict):
            print(f'{" " * d}{k}:')
            print_object(v, d + 2)
        
        else:
            print(f'{" " * d}{k}: {v}')


cursor.execute('SELECT code FROM actions')
print(set(r[0] for r in cursor.fetchall()))

cursor.execute('SELECT id FROM pages')
pages = [r[0] for r in cursor.fetchall()]
# print(f"Page IDs: {pages}")

# for page in pages:
page = 576; #pages[0] 517

def extract_page(page):
    cursor.execute(f'SELECT button_box_id FROM button_box_instances WHERE page_id={page}')
    button_box_id = cursor.fetchall()[0][0]

    cursor.execute(f'SELECT layout_x, layout_y FROM button_boxes WHERE id={button_box_id}')
    layout_x, layout_y = cursor.fetchall()[0]

    cursor.execute(f'SELECT resource_id, location, span_x, span_y FROM button_box_cells WHERE button_box_id={button_box_id}')
    cells = cursor.fetchall()
    buttons = []
    for resource_id, location, span_x, span_y in cells:
        x_pos =  location % layout_x
        y_pos = location // layout_x

        # cursor.execute(f'SELECT rid, name, type FROM resources WHERE id="{resource_id}"')
        # resource = get_object()[0]

        cursor.execute(f'SELECT * FROM buttons WHERE resource_id={resource_id}')
        button = get_object()[0]

        cursor.execute(f'SELECT * FROM button_styles WHERE id={button["button_style_id"]}')
        button['style'] = parse_obj(get_object()[0], BUTTON_STYLE_DEFAULTS)

        cursor.execute(f'SELECT * FROM symbol_links WHERE id={button["symbol_link_id"]}')
        symbol_link = get_object()
        button['symbol_link'] = symbol_link[0] if len(symbol_link) > 0 else None

        button['position'] = (x_pos, y_pos)
        button['span'] = (span_x, span_y)
        button['label'] = button.get('label', button.get('message', '')).strip()
        button['actions'] = Actions(resource_id)
        
        button = parse_obj(button, BUTTON_DEFAULTS)
        buttons.append(button)
    page = {
        'layout': (layout_x, layout_y),
        'buttons': buttons,
    }
    return page
        


def extract_deap(page_start, pages = {}):
    if page_start not in pages:
        page = extract_page(page_start)
        pages[page_start] = page
        for button in page['buttons']:
            linked_page = button['actions'].get_linked_page()
            if linked_page is not None:
                extract_deap(linked_page, pages)
    return pages




