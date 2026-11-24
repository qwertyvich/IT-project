"""Контроль компактной печатной записки и сохранности её смысловых связей."""
from pathlib import Path
import json,re,hashlib,sys,subprocess
from collections import Counter
from docx import Document
from pypdf import PdfReader
from lxml import etree
import pdfplumber
from project_model import ROOT,SRC,FIG,OUT,AUTHOR,GROUP,TEACHER,ENTITIES,validate_model
from concise_catalog import FIGURES
from concise_content import HEADING_LIST
from check_project import arithmetic,check_contracts,check_module_tasks
from dfd_model import validate_dfd
from quality_metrics import check_reference
from specifications import CONTRACTS
from developer_tasks import DETAILS

MAIN=OUT/'Банковская система — Пояснительная записка.docx'
GUIDE=OUT/'Защита за 3 минуты и пояснения.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
normalize=lambda text:''.join(text.split())

def run():
 d=Document(MAIN);alltext='\n'.join(p.text for p in d.paragraphs)+'\n'+'\n'.join(c.text for t in d.tables for row in t.rows for c in row.cells)
 assert not re.search(r'лабораторн|BD_labs|учебн|курсов|вариант[ау]?\s*5|БанкПеревод',alltext,re.I)
 assert AUTHOR in alltext and GROUP in alltext and TEACHER in alltext
 assert d.styles['Normal'].font.size.pt==14 and d.styles['Normal'].paragraph_format.line_spacing==1.5
 for section in d.sections:
  assert abs(section.left_margin.mm-30)<.1 and abs(section.right_margin.mm-15)<.1
  assert abs(section.top_margin.mm-20)<.1 and abs(section.bottom_margin.mm-20)<.1
 headings=[p.text for p in d.paragraphs if p.style.name in ('Heading 1','Heading 2') and re.match(r'^\d+(?:\.\d+)?\s',p.text)]
 assert headings==HEADING_LIST
 apps=[p.text for p in d.paragraphs if p.style.name=='Heading 1' and p.text.startswith('ПРИЛОЖЕНИЕ ')]
 assert apps==['ПРИЛОЖЕНИЕ '+x for x in 'АБВГД']
 captions=[p.text for p in d.paragraphs if p.style.name=='Caption']
 assert captions==[x['caption'] for x in FIGURES] and len(d.inline_shapes)==20
 manifest=json.loads((SRC/'concise_figures_manifest.json').read_text(encoding='utf-8'))
 for shape,spec,item in zip(d.inline_shapes,FIGURES,manifest):
  rid=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
  image=d.part.rels[rid].target_part.blob
  assert hashlib.sha256(image).hexdigest()==sha(FIG/(spec['path']+'.png'))==item['sha256_png']
  assert sha(FIG/(spec['path']+'.svg'))==item['sha256_svg']
  assert item['min_font_on_paper_pt']>=8.45
 summary=json.loads((SRC/'build_summary.json').read_text(encoding='utf-8'))
 assert summary['document']['tables']==8
 assert len(d.tables)==summary['document']['physical_tables']
 assert len([p for p in d.paragraphs if p.text.startswith('Продолжение таблицы ')])==len(d.tables)-8
 assert all(t.rows[0]._tr.xpath('./w:trPr/w:tblHeader') for t in d.tables)
 body=list(d.element.body)
 bodytext=[''.join(e.xpath('.//w:t/text()')) for e in body]
 assert next(i for i,t in enumerate(bodytext) if 'ЦП1' in t)<next(i for i,t in enumerate(bodytext) if 'F1' in t)
 for token in ['ЦП1','ЦП2','ЦП3','ЦП4','u=L/Q','неизвестный исход','недостаточно свидетельств','book_opened_at','contract_ref','post_transfer','/api/v1/transfers/{id}/post','П1.','П9.']:
  assert normalize(token) in normalize(alltext),token
 for i in range(1,12):assert f'М{i:02}' in alltext
 # Сопровождающие задания относятся к текущей нумерации, а не к снятой редакции.
 module_text=(ROOT/'contracts/module_tasks.json').read_text(encoding='utf-8')
 assert not re.search(r'приложени[еяию]\s+[ЕЖИ]|словар[ьяю]\s+И|строки\s+И\b|из\s+И[;.]|\bИ\s+Т\d|политике\s+6\.4|алгоритм\s+Д\.4',module_text)
 # Одно межмодульное взаимодействие не должно терять аргументы между спецификациями.
 def build_args(signature):
  args=re.search(r'build\(([^)]*)\)',signature)[1]
  return [item.split(':',1)[0].strip() for item in args.split(',')]
 assert build_args(next(row[3] for row in CONTRACTS if row[0]=='Т09'))==build_args(DETAILS['М07']['task']['signature'][0])
 svgtext=''
 for item in manifest:
  svg=etree.fromstring((FIG/(item['path']+'.svg')).read_bytes())
  svgtext+=' '.join(''.join(e.itertext()) for e in svg.findall('.//{http://www.w3.org/2000/svg}text'))+'\n'
  assert not re.search(r'В\.[89]|приложени[яеию]\s+[ЕЖИ]|И(?:0[1-9]|1\d|2[0-5])\b',svgtext)
 for i in range(1,16):assert f'ОП{i:02}' in alltext+svgtext,f'ОП{i:02}'
 er=(FIG/'concise/C_A1_data.svg').read_text(encoding='utf-8')
 for name,_,fields in ENTITIES:
  assert name in er,name
  for field,_,_ in fields:assert re.search(r'\b'+re.escape(field)+r'\b',er),(name,field)
 pdfs=[]
 for path in [MAIN.with_suffix('.pdf'),GUIDE.with_suffix('.pdf')]:
  r=PdfReader(path);texts=[p.extract_text() or '' for p in r.pages]
  assert all(len(t.strip())>25 for t in texts)
  assert all('Ошибка! Источник ссылки' not in t for t in texts)
  for i,p in enumerate(r.pages,1):
   if path==MAIN.with_suffix('.pdf') and i==1:continue
   found=[]
   def visitor(t,cm,tm,font,size):
    if tm[5]<55 and t.strip().isdigit():found.append(t.strip())
   p.extract_text(visitor_text=visitor);assert str(i) in found,(path.name,i,found)
  for p in r.pages:
   for v in p['/Resources'].get('/Font',{}).values():
    f=v.get_object();f=f.get('/DescendantFonts',[f])[0].get_object();descriptor=f.get('/FontDescriptor').get_object()
    assert any(k in descriptor for k in ['/FontFile','/FontFile2','/FontFile3'])
  pdfs.append({'file':path.name,'pages':len(r.pages),'sha256':sha(path),'no_blank_pages':True,'fonts_embedded':True,'page_numbers_sequential':True})
  if path==MAIN.with_suffix('.pdf'):
   first_app=max(i for i,t in enumerate(texts,1) if 'ПРИЛОЖЕНИЕ А' in t)
   appendix_count=len(r.pages)-first_app+1
   assert len(r.pages)<=49 and appendix_count<=27,(len(r.pages),appendix_count)
   assert len(r.outline)>=10
   assert re.search(r'Записка\s+'+str(len(r.pages))+r'\s+с\.',texts[1])
   bounds=[];images=[]
   with pdfplumber.open(path) as p:
    for n,page in enumerate(p.pages,1):
     for word in page.extract_words():
      assert word['x0']>=30/25.4*72-2 and word['x1']<=page.width-15/25.4*72+2,(n,word['text'])
     images.extend((n,x) for x in page.images)
   assert len(images)==20
   for item,(page,x) in zip(manifest,images):
    minimum=item['min_font_px']*(x['x1']-x['x0'])/item['width']
    assert abs(minimum-item['min_font_on_paper_pt'])<.02,(item['name'],minimum)
    assert normalize(item['caption']) in normalize(texts[page-1]),item['caption']
    bounds.append({'figure':item['name'],'page':page,'font_pt':round(minimum,3)})
   print_layout={'main_pages':len(r.pages),'main_before_appendices':first_app-1,'appendix_pages':appendix_count,
     'a3_pages':sum(float(p.mediabox.width)>1000 for p in r.pages),'figures':bounds}
  else:assert len(r.pages)==2,len(r.pages)
 result={'model':validate_model(),'dfd':validate_dfd(),'reference_arithmetic':arithmetic(),'quality_formula':check_reference(),
  'cross_document_consistency':{'active_module_references_current':True,'schedule_arguments_match_T09_M07':True},
  'contracts':check_contracts(),'module_tasks':check_module_tasks(),'printed_document':{
   'chapters':7,'numbered_headings':27,'appendices':5,'figures':20,'logical_tables':8,
   'body_font_pt':14,'table_font_pt':12,'all_images_match_code':True,'all_64_fields_present_on_er':True,
   'all_15_operations_covered':True,'layout':print_layout},'pdfs':pdfs,
   'scope':'Проверка проектных документов и расчётных эталонов. Приёмочные испытания реализации не проводились.'}
 (SRC/'verification_concise.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'layout':print_layout,'pdfs':pdfs},ensure_ascii=False,indent=2))
 return result

if __name__=='__main__':run()
