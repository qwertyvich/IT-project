"""Печатный набор: пять приложений; полные каталоги сохраняются отдельно."""

GROUPS=[('А','Диаграммы сущность–связь'),('Б','Диаграммы потоков данных'),
 ('В','Модели процессов'),('Г','Архитектурные схемы и технические решения'),
 ('Д','Порядок и условия испытаний')]

# Источник, приложение, название, бумага, ориентация, высота изображения.
SPEC=[
 ('C_A0_chen','А','Концептуальная модель данных в нотации Чена','A3','landscape',220),
 ('C_A1_data','А','Логическая модель данных банковской системы','A4','landscape',145),
 ('C_A2_quality','А','Декларативная модель оценивания качества','A4','landscape',145),
 ('B1_context','Б','Контекстная диаграмма DFD','A4','landscape',135),
 ('B2_dfd','Б','DFD первого уровня: функции обслуживания','A4','landscape',145),
 ('B9_resources','Б','DFD первого уровня: общие ресурсы','A4','landscape',145),
 ('B3_tree','Б','Декомпозиция функций','A4','landscape',145),
 ('B6_transfers','Б','DFD второго уровня: переводы','A4','landscape',145),
 ('B7_loans','Б','DFD второго уровня: договоры','A4','landscape',145),
 ('V1_service','В','Общий процесс обслуживания','A4','portrait',225),
 ('V2_clients','В','Клиент и открытие счёта','A4','portrait',225),
 ('V3_cards','В','Регистрация и состояние карты','A3','landscape',220),
 ('V4_transfers','В','Подготовка и проведение перевода','A3','landscape',220),
 ('V5_loans','В','Договор и согласованный план','A3','landscape',220),
 ('V6_reports','В','Получение документа и проверка сведений','A4','portrait',225),
 ('V7_states','В','Состояния основных объектов','A4','landscape',145),
 ('G1_architecture','Г','Облик системы, ресурсы и интерфейсы','A4','landscape',145),
 ('D2_realization','Г','Раскрытие компонентов в программные модули','A4','landscape',145),
 ('D3_transfer','Г','Алгоритм проведения перевода','A4','landscape',145),
 ('D4_schedule','Г','Алгоритм расчёта планового графика','A4','landscape',145),
 ('D7_component','Г','Детальный компонент переводов и его контракты','A3','landscape',220),
]
COUNTERS={}
FIGURES=[]
for source,letter,title,paper,orientation,height in SPEC:
 COUNTERS[letter]=COUNTERS.get(letter,0)+1
 number=COUNTERS[letter]
 name=source if source.startswith('C_A') else 'C_'+source
 FIGURES.append(dict(source_name=source,name=name,path='concise/'+name,letter=letter,
  number=number,caption=f'Рисунок {letter}.{number} — {title}',paper=paper,
  orientation=orientation,max_height_mm=height,
  max_width_mm=375 if paper=='A3' else (252 if orientation=='landscape' else 165)))

REFS={'chen':'рисунок А.1','data':'рисунок А.2','quality':'рисунок А.3','context':'рисунок Б.1',
 'dfd':'рисунки Б.2–Б.3 и Б.5–Б.6','function_tree':'рисунок Б.4',
 'process_service':'рисунки В.1–В.7','process_transfer':'рисунок В.4',
 'process_loan':'рисунок В.5','architecture':'рисунок Г.1',
 'components':'рисунок Г.2','technical_transfer':'рисунки Г.3–Г.5',
 'quality_test':'приложение Д'}
