
// NODE.js
// Here we will download squidly utilities 
import nodeFetch from 'node-fetch';
import fs from 'fs';

const BASE_URL = "https://session.squidly.com.au/main/";
const UTILITES_JS = BASE_URL + "utilities-dev.js";


async function downloadUtilities() {
    // Clean Utilities folder
    if (fs.existsSync('./WebApp/Utilities')) {
        fs.rmSync('./WebApp/Utilities', { recursive: true, force: true });
    }
    fs.mkdirSync('./WebApp/Utilities');

    const response = await nodeFetch(UTILITES_JS);
    if (!response.ok) {
        throw new Error(`Failed to download utilities: ${response.statusText}`);
    }
    const data = await response.text();
    let assets = new Set([...data.matchAll(/['"](assets\/.*)['"]/g)].map(match => match[1]));

    if (assets.size > 0) {
        // Clean assets folder
        if (fs.existsSync('./WebApp/Utilities/assets')) {
            fs.rmSync('./WebApp/Utilities/assets', { recursive: true, force: true });
        }
        fs.mkdirSync('./WebApp/Utilities/assets', { recursive: true });
        
        for (let asset of assets) {
            const assetResponse = await nodeFetch(BASE_URL + asset);
            if (!assetResponse.ok) {
                console.warn(`Failed to download asset ${asset}: ${assetResponse.statusText}`);
                continue;
            }
            const assetData = await assetResponse.text();
            fs.writeFileSync(`./WebApp/Utilities/${asset}`, assetData);
            console.log(`Downloaded asset: ${asset}`);
        }
    }

    fs.writeFileSync('./WebApp/Utilities/utilities.js', data);
    console.log('Utilities downloaded successfully.');
}

downloadUtilities().catch(error => {
    console.error('Error downloading utilities:', error);
});