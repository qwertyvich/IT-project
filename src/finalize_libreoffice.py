"""Печатная сборка без Word: обновление полей и последовательное деление таблиц."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from project_model import OUT, SRC
from render_libreoffice import render
from split_print_tables import collapse_continuations, split_tables


def main(soffice):
    document = OUT/'Банковская система — Пояснительная записка.docx'
    collapse_continuations(document)
    rounds = []
    with TemporaryDirectory(prefix='bank-lo-pagination-') as temporary:
        mapping = Path(temporary)/'tables.json'
        selected = Path(temporary)/'first.json'
        for iteration in range(1, 41):
            render(soffice, document, document.with_suffix('.pdf'), mapping)
            tables = json.loads(mapping.read_text())
            assert all(r['start'] == r['end'] for t in tables for r in t['rows']), 'Разорванная строка'
            first = next((t for t in tables if any(r['start'] > t['rows'][0]['start']
                                                   for r in t['rows'][2:])), None)
            records = {'first_only': True, 'table_count': len(tables), 'records': [first] if first else []}
            selected.write_text(json.dumps(records), encoding='utf-8')
            changed = split_tables(document, selected)
            rounds.append({'round': iteration, 'tables_split': changed})
            if not changed:
                break
        else:
            raise RuntimeError('Не стабилизировалась пагинация таблиц')
    summary_path = SRC/'build_summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    actual = len(Document(document).tables)
    summary['document'].update(physical_tables=actual, continued_parts=actual-8)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (SRC/'pagination.json').write_text(json.dumps({'engine': 'LibreOffice', 'rounds': rounds,
        'all_table_parts_fit_one_page': True, 'physical_tables': actual, 'logical_tables': 8},
        ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--soffice', required=True)
    main(parser.parse_args().soffice)
