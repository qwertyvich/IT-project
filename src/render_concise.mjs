import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const bundled=path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/package.json');
let sharp;try{sharp=(await import('sharp')).default;}catch{sharp=createRequire(bundled)('sharp');}
const manifestPath=path.join(here,'concise_figures_manifest.json');
const manifest=JSON.parse(await fs.readFile(manifestPath,'utf8'));
for(const item of manifest){
 const svg=path.join(here,'..','figures','concise',item.name+'.svg');
 const png=svg.replace(/\.svg$/,'.png');
 await sharp(svg,{density:180}).png().toFile(png);
 item.sha256_png=crypto.createHash('sha256').update(await fs.readFile(png)).digest('hex');
}
await fs.writeFile(manifestPath,JSON.stringify(manifest,null,2));
console.log(`Rendered ${manifest.length} selected PNG diagrams`);
