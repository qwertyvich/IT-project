"""Проверки проектных артефактов и эталонов; не испытания будущего банковского ПО."""
import json, hashlib, re, zipfile, sys
from pathlib import Path
from decimal import Decimal
from collections import Counter
from itertools import permutations
from lxml import etree
from docx import Document
from pypdf import PdfReader
from PIL import Image
from project_model import *
from diagram_catalog import FIGURES

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def check_arithmetic():
    initial={'A':Decimal('10000.00'),'B':Decimal('1000.00'),'C':Decimal('0.00')}
    balances=initial.copy()
    facts=[('A','B',Decimal('2500.00'),'regular'),('B','A',Decimal('2500.00'),'reversal')]
    gross=Counter();net=Counter();bykind={a:Counter() for a in initial}
    for a,b,amount,kind in facts:
        balances[a]-=amount;balances[b]+=amount
        assert sum(balances.values())==sum(initial.values())==Decimal('11000.00')
        assert min(balances.values())>=0
        for acct in (a,b):gross[acct]+=amount;bykind[acct][kind]+=amount
        net[a]-=amount;net[b]+=amount
    assert balances==initial
    assert gross['A']==gross['B']==Decimal('5000.00') and net['A']==net['B']==0
    assert bykind['A']['regular']==bykind['A']['reversal']==Decimal('2500.00')
    assert (Decimal(1)*100/3).quantize(Decimal('.01'))==Decimal('33.33')
    for schedule in permutations([('T1',7000),('T2',7000)]):
        available=10000;success=[]
        for name,amount in schedule:
            if available>=amount:available-=amount;success.append(name)
        assert available==3000 and len(success)==1
    return {'fixture_section_4_6':'verified independently with Decimal','concurrent_expected_outcomes':'both serial orders verified','acceptance_tests_of_software':False}

def check_documents():
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    main=OUT/'Пояснительная записка БанкПеревод.docx'
    guide=OUT/'Защита за 3 минуты и пояснения.docx'
    d=Document(main)
    assert len(d.inline_shapes)==len(FIGURES)==26
    assert len(d.tables)==18
    figure_order=[x['name'] for x in FIGURES]
    for shape,name in zip(d.inline_shapes,figure_order):
        rid=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
        embedded=d.part.rels[rid].target_part.blob
        assert hashlib.sha256(embedded).hexdigest()==sha(FIG/(name+'.png')),(name,'Embedded image differs from reproducible source')
    with zipfile.ZipFile(main) as z:
        xml=etree.fromstring(z.read('word/document.xml'))
        text='\n'.join(xml.xpath('//w:t/text()',namespaces=ns))
        assert '__TABLES__' not in text and '__SOURCES__' not in text and 'Ошибка! Закладка' not in text
        assert 'учебн' not in text.lower(),'Domain incorrectly framed as educational'
        assert 'приложения Е' not in text and 'Таблица Е.' not in text
        assert 'индексы order(' not in text,'Outdated table alias in index specification'
        # Атрибуты находятся на диаграммах, а не в заменяющем их словаре-таблице.
        graphical_text=''.join((FIG/(n+'.svg')).read_text(encoding='utf-8') for n in ['B4_logical_people','B5_logical_operations'])
        for entity,_,fields in ENTITIES:
            assert entity in graphical_text,entity
            for field,_,_ in fields:assert field in graphical_text,(entity,field)
        for req in REQ:assert req[0] in text,req[0]
        for case in TESTS:assert case[0] in text,case[0]
        paragraphs=[''.join(p.xpath('.//w:t/text()',namespaces=ns)) for p in xml.xpath('//w:p',namespaces=ns)]
        figcaptions=[p for p in paragraphs if p.startswith('Рисунок ')]
        assert len(figcaptions)==26 and len(set(figcaptions))==26
        assert figcaptions==[x['caption'] for x in FIGURES]
        tablecaptions=[p for p in paragraphs if p.startswith('Таблица ')]
        assert len(tablecaptions)==18 and len(set(tablecaptions))==18
        assert [int(re.match(r'Таблица (\d+)',p).group(1)) for p in tablecaptions]==list(range(1,19))
        first_app=next(i for i,p in enumerate(paragraphs) if p=='ПРИЛОЖЕНИЕ А')
        assert not any(p.startswith('Таблица ') for p in paragraphs[first_app:]),'Tables remain in graphical appendices'
        for i in range(1,19):assert any(f'в таблице {i}.' in p for p in paragraphs),(i,'Missing table reference')
        styles=etree.fromstring(z.read('word/styles.xml'))
        assert not styles.xpath('//w:pBdr',namespaces=ns),'Unexpected paragraph border'
        for stylename in ['Normal','Title','Heading 1','Heading 2']:
            current=d.styles[stylename]
            resolved=None
            while current is not None:
                rf=current.element.xpath('./w:rPr/w:rFonts')
                if rf and rf[0].get(qn('w:ascii')):
                    resolved=rf[0].get(qn('w:ascii'))
                    assert not any('theme' in a.lower() for a in rf[0].attrib)
                    break
                current=current.base_style
            assert resolved=='Times New Roman',(stylename,resolved)
    for sec in d.sections:
        assert abs(sec.left_margin.mm-30)<.1 and abs(sec.right_margin.mm-15)<.1
        assert abs(sec.top_margin.mm-20)<.1 and abs(sec.bottom_margin.mm-20)<.1
    assert abs(d.styles['Normal'].font.size.pt-14)<.1
    assert d.styles['Normal'].paragraph_format.line_spacing==1.5
    assert abs(d.styles['Normal'].paragraph_format.first_line_indent.mm-12.5)<.1
    assert all(row._tr.get_or_add_trPr().find(qn('w:cantSplit')) is not None for t in d.tables for row in t.rows)
    return {'main_docx_sha256':sha(main),'guide_docx_sha256':sha(guide),'figures':len(d.inline_shapes),'tables':len(d.tables),'embedded_images_match_sources':True,'margins_mm':[30,15,20,20],'body':'Times New Roman 14 pt, 1.5, 12.5 mm indent','no_theme_font_or_paragraph_border':True}

def check_figures():
    manifest=json.loads((SRC/'figures_manifest.json').read_text(encoding='utf-8'))
    assert len(manifest)==26
    fk=json.loads((SRC/'foreign_keys.json').read_text(encoding='utf-8'))
    assert len(fk)==17
    dot=''.join((FIG/(n+'.dot')).read_text(encoding='utf-8') for n in ['B4_logical_people','B5_logical_operations'])
    for a,f,b,p in fk:assert f'{a}:{f} -> {b}:{p}' in dot,(a,f,b,p)
    out=[]
    for item in manifest:
        svg=FIG/(item['name']+'.svg');png=svg.with_suffix('.png')
        assert sha(svg)==item['sha256_svg'],svg
        etree.fromstring(svg.read_bytes())
        with Image.open(png) as im:
            assert abs(im.width/im.height-item['width']/item['height'])<.002
            assert im.width>=3000
        assert item['min_font_px']>=15
        assert item['min_font_on_paper_pt']>=7,(item['name'],item['min_font_on_paper_pt'])
        out.append({'name':item['name'],'sha256_svg':sha(svg),'sha256_png':sha(png)})
    return out

def check_pdf(path):
    reader=PdfReader(path)
    texts=[p.extract_text() or '' for p in reader.pages]
    for i,(p,txt) in enumerate(zip(reader.pages,texts),1):
        assert len(txt.strip())>30,(i,'Blank or nearly blank page')
        if i>1:
            nums=[]
            def visitor(text,cm,tm,font,size):
                if tm[5]<55 and text.strip().isdigit():nums.append(text.strip())
            p.extract_text(visitor_text=visitor)
            assert str(i) in nums,(i,nums)
        assert 'Ошибка! Источник ссылки' not in txt and 'Error! Bookmark' not in txt
    if len(reader.pages)>10:
        assert f'{len(reader.pages)} с.' in texts[1]
    return {'file':Path(path).name,'pages':len(reader.pages),'no_empty_pages':True,'page_numbers_sequential':True}

from docx.oxml.ns import qn
if __name__=='__main__':
    report={'model':validate_model(),'arithmetic_reference':check_arithmetic(),'documents':check_documents(),'diagrams':check_figures()}
    if len(sys.argv)>1:report['rendered_pdfs']=[check_pdf(p) for p in sys.argv[1:]]
    report['scope']='Структурная верификация документов и арифметика эталонов. Приёмочные испытания программы не проводились.'
    (SRC/'Проверка проекта.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='diagrams'},ensure_ascii=False,indent=2))
