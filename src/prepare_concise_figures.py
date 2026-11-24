"""Генерация печатного набора SVG из кодовых моделей с новой нумерацией."""
from pathlib import Path
import json,re,hashlib
from lxml import etree
from project_model import FIG,SRC
from concise_catalog import FIGURES
from concise_figures import build_all

NS='http://www.w3.org/2000/svg'

def main():
 extra={x['name']:x for x in build_all(FIG/'concise')}
 original={x['name']:x for x in json.loads((SRC/'figures_manifest.json').read_text(encoding='utf-8'))}
 records=[]
 for spec in FIGURES:
  source=spec['source_name']
  data=extra.get(source,original.get(source))
  assert data,source
  source_file=(FIG/'concise' if source.startswith('C_A') else FIG)/(source+'.svg')
  root=etree.fromstring(source_file.read_bytes())
  for element in root.iter():
   if not isinstance(element.tag,str):continue
   if etree.QName(element).localname=='text':
    for node in element.iter():
     if node.text:
      node.text=node.text.replace('В.8–В.9','прочее — раздел 4').replace('на В.9','в разделе 4.4').replace('в приложении И','в разделе 6.2')
      node.text=node.text.replace('приложении Ж','разделе 6').replace('приложение Ж','раздел 6').replace('И24','П9')
    element.set('fill','black')
   fill=element.get('fill','').lower()
   if fill and fill not in {'none','white','black','#fff','#ffffff','#000','#000000','transparent'}:
    element.set('fill','#eeeeee')
   stroke=element.get('stroke','')
   if stroke and stroke!='none':element.set('stroke','black')
  # V1 больше не ссылается на два исключённых однотипных процесса.
  if source=='V1_service':
   for element in root.findall('.//{'+NS+'}text'):
    for node in element.iter():
     if node.text and 'подпроцесс по' in node.text:node.text=node.text.replace('подпроцесс по','маршруты по')
  # Условие читается внутри ромба; ограничения дат подробно заданы в 4.4 и 6.2.
  if source=='D4_schedule':
   for element in root.findall('.//{'+NS+'}text'):
    if 'Первая дата позже' in ''.join(element.itertext()):
     for child in list(element):element.remove(child)
     element.text=None;element.set('y','347.70')
     for index,line in enumerate(['Ввод','корректен?']):
      span=etree.SubElement(element,'{'+NS+'}tspan',x=element.get('x'),dy='0' if index==0 else '29.12')
      span.text=line
  path=FIG/'concise'/(spec['name']+'.svg')
  svg=etree.tostring(root,encoding='utf-8',xml_declaration=True)
  path.write_bytes(svg)
  viewbox=root.get('viewBox').split();width,height=map(float,viewbox[2:])
  fonts=[float(x) for x in re.findall(r'font-size="([\d.]+)"',svg.decode('utf-8'))]
  minimum=min(fonts)
  scale=min(spec['max_width_mm']*72/25.4/width,spec['max_height_mm']*72/25.4/height)
  assert minimum*scale>=8.45,(source,minimum*scale)
  records.append({**data,**spec,'source':'svg','width':width,'height':height,
   'min_font_px':minimum,'min_font_on_paper_pt':round(minimum*scale,2),
   'sha256_svg':hashlib.sha256(svg).hexdigest()})
 (SRC/'concise_figures_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'Prepared {len(records)} selected SVG diagrams')

if __name__=='__main__':main()
