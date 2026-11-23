"""Обновить поля, оформить продолжения таблиц и экспортировать итоговый PDF в Word."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json,subprocess,sys
from docx import Document
from project_model import SRC
from build_documents import MAIN
from split_print_tables import split_tables,collapse_continuations


def main():
    rounds=[]
    collapse_continuations(MAIN)
    with TemporaryDirectory(prefix='bank-pagination-') as temporary:
        mapping=Path(temporary)/'tables.json'
        for iteration in range(1,41):
            subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass',
                '-File',str(SRC/'render_word.ps1'),'-InputDocx',str(MAIN),
                '-OutputPdf',str(MAIN.with_suffix('.pdf')),'-Update',
                '-TableMapPath',str(mapping),'-FirstSplitOnly','-SkipPdf'],check=True)
            count=split_tables(MAIN,mapping)
            rounds.append({'round':iteration,'tables_split':count})
            if not count:break
        else:raise RuntimeError('Пагинация таблиц не стабилизировалась за 40 проходов')
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass',
        '-File',str(SRC/'render_word.ps1'),'-InputDocx',str(MAIN),
        '-OutputPdf',str(MAIN.with_suffix('.pdf')),'-Update'],check=True)
    path=SRC/'build_summary.json'
    summary=json.loads(path.read_text(encoding='utf-8'))
    actual=len(Document(MAIN).tables)
    summary['document'].update(physical_tables=actual,
        continued_parts=actual-summary['document']['tables'])
    path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (SRC/'pagination.json').write_text(json.dumps({'rounds':rounds,
        'all_table_parts_fit_one_page':rounds[-1]['tables_split']==0,
        'physical_tables':actual,'logical_tables':summary['document']['tables']},
        ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pagination':rounds,'physical_tables':actual},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
