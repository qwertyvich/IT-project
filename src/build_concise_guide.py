"""Два листа подготовки к защите; не приложение к печатной записке."""
import json,hashlib
from pypdf import PdfReader
from document_layout import Writer
from defense_guide import SPEECH
from project_model import ROOT,OUT,SRC,AUTHOR,GROUP
from concise_catalog import FIGURES

GUIDE=OUT/'Защита за 3 минуты и пояснения.docx'
MAIN=OUT/'Банковская система — Пояснительная записка.pdf'

def main():
 pages=[p.extract_text() or '' for p in PdfReader(MAIN).pages]
 keys=['1.2 Цель создания системы и решаемые задачи','Рисунок А.3','Рисунок Б.4','Рисунок В.4','Рисунок Г.1','Рисунок Г.5','ПРИЛОЖЕНИЕ Д','Рисунок А.1']
 nav={key:max(i for i,text in enumerate(pages,1) if key in text) for key in keys}
 w=Writer(auto_table_refs=False);w.flow=True;w.doc.sections[0].different_first_page_header_footer=False
 w.p('Подготовка к защите','Title',indent=0)
 w.p(AUTHOR+'; '+GROUP,indent=0,size=12,after=8)
 w.p('Смысл проекта: руководителю операционного направления нужно завершать обращения правильно при заданном составе сотрудников. Программа берёт повторяемые проверки, учёт и документы; решения и ответственность остаются у людей.')
 w.p('Покажите цепочку: интерес организатора → назначение и качество → функции и процессы → необходимые средства → компоненты и модули → измерения и решение. Одна сквозная операция — перевод; общая польза проверяется сравнением полного труда.')
 for text in [
  f"Начало: 1.2, с. {nav[keys[0]]}; качество — А.3, с. {nav[keys[1]]}; Чен — А.1, с. {nav[keys[7]]}.",
  f"Функции и процесс: Б.4, с. {nav[keys[2]]}; В.4, с. {nav[keys[3]]}.",
  f"Облик и техническая деталь: Г.1, с. {nav[keys[4]]}; Г.5, с. {nav[keys[5]]}.",
  f"Приёмка: раздел 7 и приложение Д, с. {nav[keys[6]]}.",
 ]:w.p(text,indent=0,size=12,after=4).paragraph_format.line_spacing=1.15
 w.p('Архитектура — существенные элементы, их связи и принципы работы и развития. Здесь: браузер → приложение → PostgreSQL; приложение — модульный монолит. Чен (А.1) показывает сущности и связи предметной области; А.2 — полную логическую структуру хранения.',size=12,indent=0,before=4).paragraph_format.line_spacing=1.15
 w.p('Опорные слова преподавателя', 'Heading 2')
 w.p('Новая запись 03:48–03:52: «об интересах организатора бизнеса». Старая 05:14–05:17: «Там обобщение, здесь раскрытие детали»; 27:07–27:13: «Здесь требования, а здесь измерения». Короткие фрагменты совпали в двух распознаваниях; это не заверенная стенограмма.',size=12,indent=0).paragraph_format.line_spacing=1.15
 w.p('20 %, 30 пар и 120 секунд — проектные условия для согласования. Экономия не измерена; приложение ещё предстоит реализовать. ПМИ задаёт будущие проверки. Полные технические каталоги сохранены в исходниках, в записке оставлен необходимый печатный набор.',size=12,indent=0,before=6).paragraph_format.line_spacing=1.15
 w.br();w.p('Речь на три минуты','Title',indent=0)
 for time,text in SPEECH:
  p=w.p(time,indent=0,size=12,before=5,keep=True);p.runs[0].font.bold=True
  w.p(text,indent=0,size=12,after=3).paragraph_format.line_spacing=1.15
 w.save(GUIDE)
 p=SRC/'build_summary.json';summary=json.loads(p.read_text(encoding='utf-8'))
 summary['guide']={'guide':str(GUIDE),'speech_words':sum(len(t.split()) for _,t in SPEECH),'target_pages':2}
 p.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'docs/navigation.json').write_text(json.dumps({'pdf':MAIN.name,'sha256':hashlib.sha256(MAIN.read_bytes()).hexdigest(),'pages':nav},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(summary['guide'],ensure_ascii=False))

if __name__=='__main__':main()
