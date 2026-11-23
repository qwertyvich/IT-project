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
  let svg=viz.renderString(source,{format:'svg',engine:item.engine??'dot'});
  // Частичный ключ слабой сущности Чена: пунктирное подчёркивание.
  // Координаты берутся из результата Graphviz, ширина — из метрик Arial.
  for(const partial of item.partial_keys??[]){
    const groupPattern=new RegExp(`<g\\b[^>]*>\\s*<title>${partial.node}</title>[\\s\\S]*?</g>`);
    const group=svg.match(groupPattern)?.[0];
    if(!group)throw Error('Missing partial-key node: '+partial.node);
    const position=group.match(/<text\b[^>]*\bx="([\d.-]+)"\s+y="([\d.-]+)"/);
    if(!position)throw Error('Missing partial-key label: '+partial.node);
    const x=Number(position[1]), y=Number(position[2])+3, half=partial.text_width/2;
    const underline=`<line x1="${x-half}" y1="${y}" x2="${x+half}" y2="${y}" stroke="black" stroke-width="1.4" stroke-dasharray="5 3"/>`;
    svg=svg.replace(group,group.replace('</g>',underline+'</g>'));
  }
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
