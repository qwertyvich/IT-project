import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createRequire} from 'node:module';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
process.on('uncaughtException',error=>{console.error(error.message);process.exit(1);});
let sharp;
try { sharp=(await import('sharp')).default; }
catch {
  const bundled=path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/package.json');
  sharp=createRequire(bundled)('sharp');
}
const codeDir=path.dirname(fileURLToPath(import.meta.url));
const folder=path.resolve(process.argv[2]??path.join(codeDir,'..','figures'));
const manifestPath=path.join(codeDir,'figures_manifest.json');
const manifest=JSON.parse(await fs.readFile(manifestPath,'utf8'));
const bundle=path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
let viz;
for(const file of manifest.filter(i=>i.source==='dot').map(i=>i.name+'.dot')){
  if(!viz){
    let engine;
    try {engine=await import('@viz-js/viz');}
    catch {engine=createRequire(path.join(bundle,'@viz-js/viz/package.json'))('@viz-js/viz');}
    viz=await engine.instance();
  }
  const source=await fs.readFile(path.join(folder,file),'utf8');
  const item=manifest.find(i=>i.name+'.dot'===file);
  const svg=viz.renderString(source,{format:'svg',engine:item.engine??'dot'});
  await fs.writeFile(path.join(folder,file.replace('.dot','.svg')),svg);
}
const files=manifest.map(i=>i.name+'.svg');
for(const file of files){
  let svg=await fs.readFile(path.join(folder,file),'utf8');
  const dims=svg.match(/viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"/);
  svg=svg.replace(/<svg\s+width="[^"]+"\s+height="[^"]+"/,`<svg width="${dims[1]}px" height="${dims[2]}px"`);
  await sharp(Buffer.from(svg),{limitInputPixels:false}).resize({width:6000,height:4200,fit:'inside'}).png().toFile(path.join(folder,file.replace('.svg','.png')));
}
for(const item of manifest){
  const svg=await fs.readFile(path.join(folder,item.name+'.svg'),'utf8');
  const vb=svg.match(/viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"/);
  if(!vb)throw Error('Missing viewBox: '+item.name);
  item.width=Number(vb[3]);item.height=Number(vb[4]);
  const fonts=[...svg.matchAll(/font-size="([\d.]+)"/g)].map(m=>Number(m[1]));
  item.min_font_px=Math.min(...fonts);
  item.sha256_svg=crypto.createHash('sha256').update(svg).digest('hex');
  const maxWmm=item.paper==='A3'?375:252;
  const maxHmm=item.paper==='A3'?220:135;
  item.min_font_on_paper_pt=Number((Math.min(maxWmm*72/25.4/item.width,maxHmm*72/25.4/item.height)*item.min_font_px).toFixed(2));
  item.sha256_png=crypto.createHash('sha256').update(await fs.readFile(path.join(folder,item.name+'.png'))).digest('hex');
}
await fs.writeFile(manifestPath,JSON.stringify(manifest,null,2));
console.log(`Rendered ${files.length} PNG diagrams from SVG`);
