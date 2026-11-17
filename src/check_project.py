"""Верификация проекта и независимых эталонов; не испытания банковского ПО."""
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
from datetime import date
from itertools import permutations
import json,re,hashlib,zipfile,sys
from docx import Document
from docx.oxml.ns import qn
from lxml import etree
from pypdf import PdfReader
from project_model import *
from diagram_catalog import FIGURES
from build_documents import MAIN,GUIDE

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arithmetic():
 D=Decimal
 assert D('10000')-D('2500')==D('7500') and D('1000')+D('2500')==D('3500')
 for order in permutations([7000,7000]):
  bal=10000;success=0
  for x in order:
   if bal>=x:bal-=x;success+=1
  assert bal==3000 and success==1
 dates=[date(2026,1,1),date(2026,2,1),date(2026,3,1),date(2026,4,1)]
 days=[(b-a).days for a,b in zip(dates,dates[1:])];assert days==[31,28,31]
 interest=[(debt*D('.12')*D(n)/D(365)).quantize(D('.01'),rounding=ROUND_HALF_UP) for debt,n in zip(map(D,['120000','80000','40000']),days)]
 assert interest==list(map(D,['1223.01','736.44','407.67'])) and sum(interest)==D('2367.12')
 cents=10001;parts=[cents//3,cents//3,cents-2*(cents//3)]
 assert parts==[3333,3333,3335] and sum(parts)==10001
 assert (D(100)/3).quantize(D('.01'),rounding=ROUND_HALF_UP)==D('33.33')
 return {'transfer_total':'11000.00','concurrent_final_balance':'3000.00','interest':[str(x) for x in interest],'interest_sum':str(sum(interest)),'rounding_parts':['33.33','33.33','33.35'],'software_tests_run':False}

def check_figures():
 manifest=json.loads((SRC/'figures_manifest.json').read_text(encoding='utf-8'))
 assert len(manifest)==30 and {x['name'] for x in manifest}=={x['name'] for x in FIGURES}
 for item in manifest:
  p=FIG/(item['name']+'.svg');assert sha(p)==item['sha256_svg']
  assert sha(p.with_suffix('.png'))==item['sha256_png'];etree.fromstring(p.read_bytes())
  assert item['min_font_on_paper_pt']>=7.5,(item['name'],item['min_font_on_paper_pt'])
 dots=''.join((FIG/(n+'.dot')).read_text(encoding='utf-8') for n in ['A4_logical_people','A5_logical_products'])
 for a,f,b,p in FK:assert f'{a}:{f} -> {b}:{p}' in dots,(a,f,b,p)
 logical=''.join((FIG/(n+'.svg')).read_text(encoding='utf-8') for n in ['A4_logical_people','A5_logical_products'])
 for name,title,fields in ENTITIES:
  assert name in logical
  for field,_,_ in fields:assert field in logical,(name,field)
 arch=(FIG/'G1_architecture.svg').read_text(encoding='utf-8')
 for c,*_ in COMPONENTS:assert c in arch
 assert all(t not in arch for t in ['PostgreSQL','FastAPI','Docker','backend','frontend'])
 detail=(FIG/'D2_realization.svg').read_text(encoding='utf-8')
 for m,*_ in MODULES:assert m in detail,m
 algo=(FIG/'D3_transfer.svg').read_text(encoding='utf-8')
 assert 'order_id' not in algo and 'Создать transfer' not in algo
 assert 'Установить completed' in algo
 return {'diagrams':30,'all_12_foreign_keys_drawn':True,'all_attributes_present':True,'all_components_and_modules_present':True,'minimum_font_on_paper_pt':min(x['min_font_on_paper_pt'] for x in manifest)}

def check_docx():
 d=Document(MAIN);g=Document(GUIDE)
 paragraphs=[p.text for p in d.paragraphs]
 alltext='\n'.join(paragraphs+[' '.join(c.text for row in t.rows for c in row.cells) for t in d.tables])
 assert TOPIC in alltext and AUTHOR in alltext and GROUP in alltext and TEACHER in alltext
 assert 'М8О-309БВ-24' not in alltext and 'учебн' not in alltext.lower()
 assert 'БанкПеревод' not in alltext and 'beneficiary' not in alltext and 'transfer_reversal' not in alltext
 assert len(d.inline_shapes)==len(FIGURES)==30
 for shape,f in zip(d.inline_shapes,FIGURES):
  rid=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
  assert hashlib.sha256(d.part.rels[rid].target_part.blob).hexdigest()==sha(FIG/(f['name']+'.png'))
 captions=[p.text for p in d.paragraphs if p.style.name=='Caption']
 assert captions==[f['caption'] for f in FIGURES]
 assert len(d.tables)==41,len(d.tables)
 assert [p.text for p in d.paragraphs if p.style.name=='Heading 1' and p.text.startswith('ПРИЛОЖЕНИЕ ')]==['ПРИЛОЖЕНИЕ '+x for x in 'АБВГДЕ']
 for r in REQ:assert r[0] in alltext,r[0]
 for case in TESTS:assert case[0]+' '+case[1] in alltext,case[0]
 for leaf in LEAVES:assert leaf[0] in alltext,leaf[0]
 for m,title,*_ in MODULES:assert m+' '+title in alltext,m
 assert d.styles['Normal'].font.size.pt==14 and d.styles['Normal'].paragraph_format.line_spacing==1.5
 for s in d.sections:
  assert abs(s.left_margin.mm-30)<.1 and abs(s.right_margin.mm-15)<.1
  assert abs(s.top_margin.mm-20)<.1 and abs(s.bottom_margin.mm-20)<.1
 for name in ['Normal','Title','Heading 1','Heading 2']:
  st=d.styles[name];found=False
  while st is not None:
   fonts=st.element.xpath('./w:rPr/w:rFonts')
   if fonts and fonts[0].get(qn('w:ascii')):
    assert fonts[0].get(qn('w:ascii'))=='Times New Roman';found=True;break
   st=st.base_style
  assert found
 with zipfile.ZipFile(MAIN) as z:
  assert b'pBdr' not in z.read('word/styles.xml')
 assert AUTHOR in '\n'.join(p.text for p in g.paragraphs)
 return {'main_docx_sha256':sha(MAIN),'guide_docx_sha256':sha(GUIDE),'figures':30,'tables':41,'appendices':6,'author':AUTHOR,'group':GROUP,'images_match_sources':True}

def check_pdf(path):
 r=PdfReader(path);texts=[p.extract_text() or '' for p in r.pages]
 assert AUTHOR in texts[0] and GROUP in texts[0]
 assert all(len(x.strip())>25 for x in texts)
 assert all('Ошибка! Источник ссылки' not in x and 'Error! Bookmark' not in x for x in texts)
 for i,p in enumerate(r.pages[1:],2):
  nums=[]
  def visitor(text,cm,tm,font,size):
   if tm[5]<55 and text.strip().isdigit():nums.append(text.strip())
  p.extract_text(visitor_text=visitor);assert str(i) in nums,(i,nums)
 assert len(r.outline)>5,len(r.outline)
 fonts={}
 for page in r.pages:
  for item in page['/Resources'].get('/Font',{}).values():
   font=item.get_object();name=str(font.get('/BaseFont','unknown'))
   base=font.get('/DescendantFonts',[font])[0].get_object()
   descriptor=base.get('/FontDescriptor')
   embedded=bool(descriptor and any(k in descriptor.get_object() for k in ['/FontFile','/FontFile2','/FontFile3']))
   assert embedded,(path,name)
   fonts[name]=embedded
 return {'file':Path(path).name,'pages':len(r.pages),'outline_present':True,'no_blank_pages':True,'page_numbers_sequential':True,'fonts_embedded':fonts,'sha256':sha(path)}

if __name__=='__main__':
 result={'model':validate_model(),'reference_arithmetic':arithmetic(),'diagrams':check_figures(),'documents':check_docx()}
 pdf_paths=sys.argv[1:] or [p for p in [MAIN.with_suffix('.pdf'),GUIDE.with_suffix('.pdf')] if p.is_file()]
 if pdf_paths:result['pdfs']=[check_pdf(p) for p in pdf_paths]
 result['scope']='Проверка проектных артефактов и независимых эталонов. Приёмочные испытания банковского ПО не проводились.'
 (SRC/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
