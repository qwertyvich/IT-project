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
from dfd_model import validate_dfd,BOUNDARY,NAMES,LEAF_TITLES
from business_case import OPERATIONS
from specifications import field_rows,CONTRACTS,EXAMPLES
from quality_metrics import check_reference

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
 assert len(manifest)==36 and {x['name'] for x in manifest}=={x['name'] for x in FIGURES}
 for item in manifest:
  p=FIG/(item['name']+'.svg');assert sha(p)==item['sha256_svg']
  assert sha(p.with_suffix('.png'))==item['sha256_png'];etree.fromstring(p.read_bytes())
  assert item['min_font_on_paper_pt']>=7.5,(item['name'],item['min_font_on_paper_pt'])
 dots=''.join((FIG/(n+'.dot')).read_text(encoding='utf-8') for n in ['A4_logical_people','A5_logical_products'])
 chen=next(item for item in manifest if item['name']=='A2_products')
 assert chen['partial_keys'][0]['node']=='schedule_a0'
 assert 'stroke-dasharray="5 3"' in (FIG/'A2_products.svg').read_text(encoding='utf-8')
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
 for parent,flows in BOUNDARY.items():
  svg=etree.fromstring((FIG/(NAMES[parent]+'.svg')).read_bytes())
  visible=' '.join(' '.join(''.join(e.itertext()) for e in svg.findall('.//{http://www.w3.org/2000/svg}text')).split())
  for code in flows:assert code in visible,(parent,code)
  for leaf,title in LEAF_TITLES.items():
   if leaf.startswith(parent+'.'):assert leaf+' '+title in visible,(leaf,title)
 processes=[x for x in manifest if x['name'].startswith('V') and x['name']!='V7_states']
 drawn_ops=set()
 for item in processes:
  assert item['sequence_connected'] and item['data_objects']==2,item['name']
  assert item['data_inputs']==1 and item['data_outputs']==1,item['name']
  svg=(FIG/(item['name']+'.svg')).read_text(encoding='utf-8')
  for op in item['operations']:assert op in svg;drawn_ops.add(op)
 assert drawn_ops=={f'ОП{i:02}' for i in range(1,16)},drawn_ops
 assert {x[0] for x in OPERATIONS}=={x[0] for x in LEAVES}
 assert len({x[1].split(';')[0] for x in OPERATIONS})==15
 expected_files={x['name']+ext for x in manifest for ext in (['.svg','.png','.dot'] if x['source']=='dot' else ['.svg','.png'])}
 assert {p.name for p in FIG.iterdir() if p.is_file()}==expected_files
 return {'diagrams':len(manifest),'all_12_foreign_keys_drawn':True,'all_attributes_present':True,'all_components_and_modules_present':True,'all_15_operations_drawn':True,'dfd':validate_dfd(),'minimum_font_on_paper_pt':min(x['min_font_on_paper_pt'] for x in manifest)}

def check_docx():
 d=Document(MAIN);g=Document(GUIDE)
 paragraphs=[p.text for p in d.paragraphs]
 alltext='\n'.join(paragraphs+[' '.join(c.text for row in t.rows for c in row.cells) for t in d.tables])
 assert TOPIC in alltext and AUTHOR in alltext and GROUP in alltext and TEACHER in alltext
 assert 'М8О-309БВ-24' not in alltext and 'учебн' not in alltext.lower()
 assert not re.search(r'лабораторн|BD_labs|\bЛР\s*[12]|вариант[ау]?\s*5|курсов|учебн',alltext,re.I)
 from report_content import SOURCES
 citation_groups=re.findall(r'\[([\d,\s–-]+)\]',alltext)
 citations={int(x) for group in citation_groups for x in re.findall(r'\d+',group)}
 assert citations and min(citations)>=1 and max(citations)<=len(SOURCES)==16,citations
 assert 'БанкПеревод' not in alltext and 'beneficiary' not in alltext and 'transfer_reversal' not in alltext
 assert len(d.inline_shapes)==len(FIGURES)==36
 for shape,f in zip(d.inline_shapes,FIGURES):
  rid=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
  assert hashlib.sha256(d.part.rels[rid].target_part.blob).hexdigest()==sha(FIG/(f['name']+'.png'))
 captions=[p.text for p in d.paragraphs if p.style.name=='Caption']
 assert captions==[f['caption'] for f in FIGURES]
 summary=json.loads((SRC/'build_summary.json').read_text(encoding='utf-8'))
 assert len(d.tables)==summary['document']['tables'],len(d.tables)
 assert [p.text for p in d.paragraphs if p.style.name=='Heading 1' and p.text.startswith('ПРИЛОЖЕНИЕ ')]==['ПРИЛОЖЕНИЕ '+x for x in 'АБВГДЕЖИ']
 for r in REQ:assert r[0] in alltext,r[0]
 for case in TESTS:assert case[0]+' '+case[1] in alltext,case[0]
 for leaf in LEAVES:assert leaf[0] in alltext,leaf[0]
 for m,title,*_ in MODULES:assert m+' '+title in alltext,m
 reference=json.loads((ROOT/'docs/reference_structure.json').read_text(encoding='utf-8'))
 headings=[p.text for p in d.paragraphs if p.style.name in ('Heading 1','Heading 2') and re.match(r'^\d+\s|^\d+\.\d+\s',p.text)]
 assert headings==reference['expected_headings'],headings
 # Критерии назначения должны быть заданы до перечня функциональных требований.
 # Ищем фактические элементы документа, а не строки обновлённого оглавления.
 body=list(d.element.body)
 h13=next(i for i,e in enumerate(body) if e.tag==qn('w:p') and ''.join(e.xpath('.//w:t/text()'))=='1.3 Функциональные требования')
 goal_caption=next(i for i,e in enumerate(body) if 'Критерии достижения назначения' in ''.join(e.xpath('.//w:t/text()')))
 assert goal_caption<h13,'Внешние критерии оказались после функциональных требований'
 assert alltext.index('1.4 Нефункциональные требования и критерии качества',alltext.index('ВВЕДЕНИЕ'))<alltext.index('3 Модель функционирования системы',alltext.index('ВВЕДЕНИЕ'))
 for token in ['БП-01','Г0','ЦП1','ЦП2','ЦП3','ЦП4','u_B≤0,80u_A','недостаточно свидетельств']:
  assert token in alltext,token
 for _,o,_,_,_,handler,_ in OPERATIONS:
  assert o.split(';')[0] in alltext and handler in alltext,o
 for table_name,_,fields in ENTITIES:
  assert table_name in alltext
  for field,_,_ in fields:assert field in alltext,(table_name,field)
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
 return {'main_docx_sha256':sha(MAIN),'guide_docx_sha256':sha(GUIDE),'figures':len(FIGURES),'tables':len(d.tables),'chapters':7,'numbered_headings':len(headings),'reference_structure_verified':True,'appendices':8,'author':AUTHOR,'group':GROUP,'images_match_sources':True}

def check_contracts():
 data=json.loads((ROOT/'contracts/openapi.json').read_text(encoding='utf-8'))
 assert data['openapi']=='3.1.0' and len(field_rows())==64
 assert data['paths']['/transfers/{id}']['get']['responses']['200']['content']['application/json']['schema']['$ref']=='#/components/schemas/TransferView'
 schemas=data['components']['schemas']
 assert 'contract_ref' in schemas['LoanCommand']['required'] and 'contract_ref' in schemas['LoanView']['required']
 assert 'created_by' in schemas['LoanView']['required']
 assert dict((f,flags) for f,_,flags in next(e[2] for e in ENTITIES if e[0]=='loan'))['contract_ref']=='UQ, NN'
 def resolve(schema):
  if '$ref' in schema:
   assert schema['$ref'].startswith('#/components/schemas/')
   return schemas[schema['$ref'].split('/')[-1]]
  return schema
 def validate(value,schema):
  schema=resolve(schema)
  if 'const' in schema:assert value==schema['const']
  if 'enum' in schema:assert value in schema['enum']
  kind=schema.get('type')
  if kind=='object':
   assert isinstance(value,dict)
   assert set(schema['required'])<=set(value)
   if schema.get('additionalProperties') is False:assert set(value)<=set(schema['properties'])
   for k,v in value.items():validate(v,schema['properties'][k])
  elif kind=='string':
   assert isinstance(value,str)
   # JSON Schema pattern ищет совпадение; полное совпадение задаётся якорями.
   if 'pattern' in schema:assert re.search(schema['pattern'],value),value
   if schema.get('format')=='uuid':
    from uuid import UUID
    UUID(value)
   if schema.get('format')=='date':date.fromisoformat(value)
   if schema.get('format')=='date-time':
    from datetime import datetime
    assert datetime.fromisoformat(value).tzinfo is not None
  elif kind=='integer':assert type(value) is int and value>=schema.get('minimum',value) and value<=schema.get('maximum',value)
  elif kind=='array':
   assert isinstance(value,list) and len(value)>=schema.get('minItems',0)
   for item in value:validate(item,schema['items'])
 def walk(node):
  if isinstance(node,dict):
   if '$ref' in node:resolve(node)
   if node.get('type')=='object':assert set(node['required'])<=set(node['properties'])
   for child in node.values():walk(child)
  elif isinstance(node,list):
   for child in node:walk(child)
 walk(data)
 for (_,example),name in zip(EXAMPLES,['TransferCommand','PostingResult','Error','LoanCommand']):validate(example,schemas[name])
 assert len(CONTRACTS)==11 and {c[0] for c in CONTRACTS}=={f'Т{i:02}' for i in range(1,12)}
 return {'fields_defined':64,'interface_contracts':11,'openapi_examples_checked':4,'loan_source_reference_required':True,'all_local_schema_references_resolve':True,'scope':'Структурная проверка спецификации и примеров; не сертификация OpenAPI и не проверка работающего API.'}

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
 result={'model':validate_model(),'reference_arithmetic':arithmetic(),'quality_formula':check_reference(),'diagrams':check_figures(),'contracts':check_contracts(),'documents':check_docx()}
 pdf_paths=sys.argv[1:] or [p for p in [MAIN.with_suffix('.pdf'),GUIDE.with_suffix('.pdf')] if p.is_file()]
 if pdf_paths:result['pdfs']=[check_pdf(p) for p in pdf_paths]
 result['scope']='Проверка проектных артефактов и независимых эталонов. Приёмочные испытания банковского ПО не проводились.'
 (SRC/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
