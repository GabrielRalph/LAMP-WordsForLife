require('dotenv').config({ path: '../Firebase Functions/function-tests/test.env' });
const FB = require('../Firebase Functions/functions/firebase');
const fs = require('fs');
const { getDownloadURL } = require("../Firebase Functions/functions/node_modules/firebase-admin/lib/storage");

async function checkFileExistsInDB(filepath) {
    let iconFile = FB.sb.file(`LampIcons/${filepath}`);
    const [exists] = await iconFile.exists();
    return exists;
}

async function uploadIcon(filepath, databasePath, url) {
    let iconFile = FB.sb.file(`LampIcons/${databasePath}`);
    const [exists] = await iconFile.exists();
    if (!exists) {
        let dataBuffer = fs.readFileSync(filepath);
        await iconFile.save(dataBuffer, {
            metadata: {
                contentType: 'image/png',
            }
        });
    }
    url = await getDownloadURL(iconFile);
    return url;
}

const iconDirKeys = {
    "#": "CLTY",
    "@": "MTC",
    "!": "PCS",
    "-": "PRC",
    "{": "WDGT",
    "^": "SYBX",
}
function iconDir(icon_file) {
    let key = icon_file[icon_file.length - 1];
    let dir = iconDirKeys[key] || "SCSH";
    // check file exists in that dir
    let filepath = `./NuVoiceAPp/IconsExtracted/${dir}/${icon_file}.png`;
    if (fs.existsSync(filepath)) {
        return {filepath, dbPath: `${dir}/${icon_file}.png`};
    } else {
        return null;
    }
}

async function uploadeAllUsedIcons(file = './pages_with_icons.json') {
    const pagesWithIcons = require(file);


    let files = {}
    let buttonsToUpdate = [];
    for (const page in pagesWithIcons) {
        for (const button of pagesWithIcons[page].buttons) {
            const {icon_file, icon_url} = button;
            if (!icon_url && typeof icon_file === 'string' && icon_file.length > 0) {
                files[icon_file] = false;
                buttonsToUpdate.push(button);
            }
        }
    }
    console.log(`Found ${Object.keys(files).length} unique icons to upload.`);

    let printStatus = () => {
        let total = Object.keys(files).length;
        let uploaded = Object.values(files).filter(url => url !== false).length;
        process.stdout.write(`Uploaded ${uploaded}/${total} icons\r`);
    }

    let upload = async (icon_file) => {
        let dir = iconDir(icon_file);
        if (dir === null) {
            console.log(`Icon file not found for ${icon_file}`);
        } else {
            try {
                let url = await uploadIcon(dir.filepath, dir.dbPath);
                files[icon_file] = url;
                printStatus();
            } catch (error) {
                console.error(`Error uploading ${icon_file}`);
                files[icon_file] = null;
            }
        }
    };

    const chunkSize = 50;
    for (let i = 0; i < Object.keys(files).length; i += chunkSize) {
        let chunk = Object.keys(files).slice(i, i + chunkSize);
        await Promise.all(chunk.map(upload));
    }
    
    for (const button of buttonsToUpdate) {
        button.icon_url = files[button.icon_file];
    }

    fs.writeFileSync(file, JSON.stringify(pagesWithIcons, null, 2));
}

uploadeAllUsedIcons("./zuns_lamp_pages.json");