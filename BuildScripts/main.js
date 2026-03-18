
// NODE.js
// Here we will download squidly utilities 
import nodeFetch from 'node-fetch';
import fs from 'fs';

const URL = "https://session.squidly.com.au/main/utilities-dev.js";

async function downloadUtilities() {
    const response = await nodeFetch(URL);
    if (!response.ok) {
        throw new Error(`Failed to download utilities: ${response.statusText}`);
    }
    const data = await response.text();
    fs.writeFileSync('./WebApp/utilities.js', data);
    console.log('Utilities downloaded successfully.');
}

downloadUtilities().catch(error => {
    console.error('Error downloading utilities:', error);
});