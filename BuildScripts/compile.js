import fs from 'fs';

const liveURL = `"https://session.squidly.com.au/main/utilities.js"`;
let indexJS = fs.readFileSync('./WebApp/index.js', 'utf-8');
indexJS = indexJS.replace(/"\.\/Utilities\/utilities\.js"/, liveURL);
fs.writeFileSync('./WebApp/index.js', indexJS);

// Delete the utilities.js file if it exists
if (fs.existsSync('./WebApp/Utilities')) {
    fs.rmSync('./WebApp/Utilities', { recursive: true, force: true });
    console.log('Deleted local utilities.js file.');
} else {
    console.log('No local utilities.js file found to delete.');
}
