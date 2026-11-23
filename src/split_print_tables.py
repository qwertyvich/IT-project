"""Оформить продолжения таблиц по фактической пагинации Word, сохраняя строки."""
from copy import deepcopy
from pathlib import Path
import json,re,sys
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def collapse_continuations(document_path):
    """Перед новой пагинацией восстановить целые логические таблицы."""
    doc=Document(document_path);removed=0
    for paragraph in list(doc.paragraphs):
        if not paragraph.text.startswith('Продолжение таблицы '):continue
        element=paragraph._p;previous=element.getprevious();following=element.getnext()
        assert previous.tag==qn('w:tbl') and following.tag==qn('w:tbl')
        rows=list(following.findall(qn('w:tr')))
        for row in rows[1:]:previous.append(deepcopy(row))
        element.getparent().remove(following);element.getparent().remove(element);removed+=1
    if removed:doc.save(document_path)
    return removed


def split_tables(document_path,map_path):
    document_path=Path(document_path)
    doc=Document(document_path)
    records=json.loads(Path(map_path).read_text(encoding='utf-8-sig'))
    first_only=isinstance(records,dict) and records.get('first_only')
    if first_only:
        assert len(doc.tables)==records['table_count']
        records=records['records']
    else:
        if isinstance(records,dict):records=[records]
        assert len(doc.tables)==len(records),(len(doc.tables),len(records))
    changed=0
    for item in reversed(records):
        table=doc.tables[item['table']-1]._tbl
        rows=list(table.findall(qn('w:tr')))
        assert len(rows)==len(item['rows'])
        # Шапка + хотя бы одна строка остаются вместе.
        first_page=item['rows'][0]['start']
        cut=next((i for i,r in enumerate(item['rows']) if i>1 and r['start']>first_page),None)
        assert all(r['start']==r['end'] for r in item['rows']),'Одна строка разорвана между страницами'
        if cut is None:continue
        previous=table.getprevious()
        while previous is not None and not ''.join(previous.xpath('.//w:t/text()')).strip():previous=previous.getprevious()
        caption=''.join(previous.xpath('.//w:t/text()')) if previous is not None else ''
        match=re.match(r'(?:Таблица|Продолжение таблицы)\s+([А-ЯA-Z]\.\d+|\d+)',caption)
        assert match,caption
        number=match.group(1)
        continuation=deepcopy(table)
        for row in list(continuation.findall(qn('w:tr'))):continuation.remove(row)
        continuation.append(deepcopy(rows[0]))
        for row in rows[cut:]:
            continuation.append(deepcopy(row));table.remove(row)
        p=OxmlElement('w:p');properties=OxmlElement('w:pPr')
        for tag in ['pageBreakBefore','keepNext']:
            properties.append(OxmlElement('w:'+tag))
        ind=OxmlElement('w:ind');ind.set(qn('w:firstLine'),'0');properties.append(ind)
        spacing=OxmlElement('w:spacing');spacing.set(qn('w:before'),'0');spacing.set(qn('w:after'),'60');spacing.set(qn('w:line'),'240');spacing.set(qn('w:lineRule'),'auto');properties.append(spacing)
        p.append(properties)
        run=OxmlElement('w:r');pr=OxmlElement('w:rPr');size=OxmlElement('w:sz');size.set(qn('w:val'),'24');pr.append(size);run.append(pr)
        text=OxmlElement('w:t');text.text='Продолжение таблицы '+number;run.append(text);p.append(run)
        table.addnext(p);p.addnext(continuation);changed+=1
    assert not first_only or not records or changed==1,'Не удалось разделить обнаруженную многостраничную таблицу'
    if changed:doc.save(document_path)
    return changed


if __name__=='__main__':
    changed=split_tables(sys.argv[1],sys.argv[2])
    summary_path=Path(__file__).with_name('build_summary.json')
    summary=json.loads(summary_path.read_text(encoding='utf-8'))
    actual=len(Document(sys.argv[1]).tables)
    summary['document']['physical_tables']=actual
    summary['document']['continued_parts']=actual-summary['document']['tables']
    summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'split_tables':changed,'physical_tables':actual},ensure_ascii=False))
