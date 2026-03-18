const data = require('./pages_with_icons_updated.json');

for (const page in data) {
    for (const button of data[page].buttons) {
        let {label, message, actions} = button;
        if (actions.indexOf('C10') !== -1) { 
            message = message || label || '';
            if (message[message.length - 1] !== ' ' && message.length > 1) {
                button.message = message + ' ';
            }
        }
    }
}

const fs = require('fs');
fs.writeFileSync('./lamp_pages.json', JSON.stringify(data, null, 2));