GROUPS=[
 ('А','Документы и декларативная модель',[
  ('A1_people','Модель Чена: отделения, клиенты, счета и сотрудники','A3'),
  ('A2_products','Модель Чена: карты, переводы и кредитные договоры','A3'),
  ('A3_quality','Модель Чена системы оценивания качества','A3'),
  ('A4_logical_people','Логическая модель клиентского контекста','A4'),
  ('A5_logical_products','Логическая модель операций, продуктов и аудита','A3')]),
 ('Б','Функциональная модель',[
  ('B1_context','Контекстная диаграмма DFD','A3'),
  ('B2_dfd','DFD первого уровня: банковское обслуживание','A3'),
  ('B3_tree','Дерево декомпозиции функций','A3'),
  ('B4_clients','DFD второго уровня: клиенты и счета','A3'),
  ('B5_cards','DFD второго уровня: банковские карты','A3'),
  ('B6_transfers','DFD второго уровня: переводы','A3'),
  ('B7_loans','DFD второго уровня: кредитные договоры','A3'),
  ('B8_reports','DFD второго уровня: сведения и контроль','A3'),
  ('B9_resources','DFD первого уровня: общие ресурсы и ответственность','A3')]),
 ('В','Процессная модель',[
  ('V1_service','BPMN: полный маршрут банковского обслуживания','A3'),
  ('V2_clients','BPMN: клиент и открытие счёта','A3'),
  ('V3_cards','BPMN: регистрация и состояние карты','A3'),
  ('V4_transfers','BPMN: подготовка и проведение перевода','A3'),
  ('V5_loans','BPMN: договор и согласованный график','A3'),
  ('V6_reports','BPMN: получение проверяемого отчёта','A3'),
  ('V7_states','Состояния переводов, карт и договоров','A3'),
  ('V8_reference','BPMN: отделения, сотрудники и доступ','A3'),
  ('V9_close','BPMN: закрытие кредитного договора по основанию','A3')]),
 ('Г','Архитектура системы',[
  ('G1_architecture','Облик системы: компоненты, связи и интерфейсы','A3'),
  ('G2_functioning','Обобщённая модель функционирования','A3'),
  ('G3_reasoning','Сквозное обоснование решений и качества','A3'),
  ('G4_business','Внешнее назначение и противоречие организатора','A3'),
  ('G5_quality','Концепция качества и проверка интереса заказчика','A3')]),
 ('Д','Технический проект',[
  ('D1_deployment','Техническое размещение компонентов','A3'),
  ('D2_realization','Раскрытие компонентов архитектуры в программные модули','A3'),
  ('D3_transfer','Алгоритм проведения перевода','A4'),
  ('D4_schedule','Алгоритм расчёта планового графика','A3'),
  ('D5_concurrency','Два конкурентных списания общего счёта','A4'),
  ('D6_sequence','Последовательность сквозного проведения перевода','A3'),
  ('D7_component','Техническая декомпозиция компонента переводов и контракты','A3')]),
 ('Е','Программа и методика испытаний',[
  ('E1_quality','Получение свидетельств и решение о качестве','A3')]),
]
FIGURES=[dict(name=n,caption=f'Рисунок {letter}.{i} — {title}',paper=paper,letter=letter) for letter,_,items in GROUPS for i,(n,title,paper) in enumerate(items,1)]
BY_NAME={x['name']:x for x in FIGURES}

# Печатный формат выбирается по фактической геометрии и размеру подписей.
# Подробные модели сохраняют A3; компактные представления печатаются на A4.
A4_LANDSCAPE={
 'A4_logical_people','B1_context','B2_dfd','B3_tree','B4_clients','B5_cards',
 'B6_transfers','B7_loans','B8_reports','B9_resources','V7_states',
 'G1_architecture','G2_functioning','G3_reasoning','G4_business','G5_quality','D1_deployment','D2_realization','D3_transfer',
 'D4_schedule','D5_concurrency','D6_sequence','E1_quality',
}
A4_PORTRAIT={'V1_service','V2_clients','V6_reports','V8_reference','V9_close'}
for figure in FIGURES:
 if figure['name'] in A4_LANDSCAPE:
  figure.update(paper='A4',orientation='landscape',max_width_mm=252,max_height_mm=135 if figure['name'] in {'A4_logical_people','B1_context'} else 145)
 elif figure['name'] in A4_PORTRAIT:
  figure.update(paper='A4',orientation='portrait',max_width_mm=165,max_height_mm=225)
 else:
  figure.update(paper='A3',orientation='landscape',max_width_mm=375,max_height_mm=220)
