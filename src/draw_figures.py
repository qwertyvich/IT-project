"""Воспроизводимые графические модели банковской системы из единой спецификации."""
import html,json,math,hashlib,ast
from pathlib import Path
from PIL import ImageFont
from fonts import ARIAL
from project_model import *
from diagram_catalog import FIGURES,BY_NAME
from diagram_tools import Graph,Picture,BPMN,BLUE,YELLOW,GREEN,wrap
import svg_primitives as primitive
import dfd_figures
import process_figures
import additional_figures

def chen(name,entities,relations,places,rplaces):
 g=Graph(name,'TB',26);g.body.append('graph [overlap=true, splines=true];');partial_keys=[]
 def pos(id,xy):g.body.append(f'{id} [pos="{xy[0]/72},{xy[1]/72}!",pin=true];')
 for id,title,attrs in entities:
  weak=id=='schedule'
  g.node(id,title,'box',BLUE,**({'peripheries':2} if weak else {}));cx,cy=places[id];pos(id,(cx,cy))
  offsets=([(0,230),(-310,140),(310,140),(-290,340),(290,340),(0,460)] if cy>800 else [(0,-210),(-310,-120),(310,-120),(-280,-320),(280,-320),(0,-440)])
  for i,t in enumerate(attrs):
   aid=f'{id}_a{i}';key=t.startswith('*');t=t.lstrip('*')
   if key and weak:
    g.node(aid,t,'ellipse','white')
    partial_keys.append({'node':aid,'text_width':ImageFont.truetype(str(ARIAL),26).getlength(t)})
   elif key:
    g.nodes.add(aid);g.body.append(f'{aid} [shape=ellipse,label=<<U>{html.escape(t)}</U>>,style=filled,fillcolor=white];')
   else:g.node(aid,t,'ellipse','white')
   dx,dy=offsets[i];pos(aid,(cx+dx,cy+dy));g.edge(id,aid,'',dir='none',color='#555555')
 for i,(a,b,t,ca,cb) in enumerate(relations):
  rid='r'+str(i);g.node(rid,t,'diamond',YELLOW,margin='.03,.02',**({'peripheries':2} if b=='schedule' else {}));pos(rid,rplaces[i])
  g.edge(a,rid,'',dir='none',headlabel=ca,labeldistance='2',labelangle='35')
  g.edge(rid,b,'',dir='none',taillabel=cb,labeldistance='2',labelangle='35',**({'color':'black:white:black'} if b=='schedule' else {}))
 result=g.save();result['engine']='neato'
 if partial_keys:result['partial_keys']=partial_keys
 return result

def declarative():
 out=[]
 out.append(chen('A1_people',[
  ('branch','ОТДЕЛЕНИЕ\nbranch',['*Код отделения','Город','Адрес']),
  ('client','КЛИЕНТ\nclient',['*Идентификатор клиента','ФИО','Телефон','Email','Дата регистрации']),
  ('account','СЧЁТ\naccount',['*Номер счёта','Начальный остаток','Текущий остаток','Состояние','Дата открытия']),
  ('employee','СОТРУДНИК\nemployee',['*Идентификатор сотрудника','ФИО','Логин','Роль','Признак активности'])],
  [('branch','account','ВЕДЁТ','1','0..N'),('client','account','ВЛАДЕЕТ','1','0..N'),('branch','employee','ОБЪЕДИНЯЕТ\nСОТРУДНИКОВ','1','0..N')],
  {'branch':(450,1250),'client':(1650,1250),'account':(1650,400),'employee':(450,400)},[(1050,800),(1650,830),(450,830)]))
 out.append(chen('A2_products',[
  ('card','БАНКОВСКАЯ КАРТА\nbank_card',['*Номер карты','Дата выпуска','Дата окончания','Состояние']),
  ('transfer','ПЕРЕВОД\ntransfer',['*Идентификатор перевода','Сумма','Состояние','Ключ запроса','Дата инициирования','Дата завершения']),
  ('loan','КРЕДИТНЫЙ ДОГОВОР\nloan',['*Номер договора','Основная сумма','Годовая ставка','Дата начала договора','Срок окончания','Основание закрытия']),
  ('account','СЧЁТ\nконтекст А.1',['*Номер счёта']),
  ('employee','СОТРУДНИК\nконтекст А.1',['*Идентификатор сотрудника']),
  ('schedule','ПЛАНОВЫЙ ПЛАТЁЖ\nloan_schedule',['*Номер в договоре','Дата платежа','Основная часть','Процентная часть'])],
  [('account','card','ОБСЛУЖИВАЕТСЯ\nКАРТОЙ','1','0..N'),('account','transfer','ОТПРАВИТЕЛЬ','1','0..N'),('account','transfer','ПОЛУЧАТЕЛЬ','1','0..N'),
   ('account','loan','УКАЗАН\nВ ДОГОВОРЕ','1','0..N'),('loan','schedule','СОДЕРЖИТ\nПЛАН','1','1..N'),('employee','card','РЕГИСТРИРУЕТ\nКАРТУ','1','0..N'),
   ('employee','transfer','СОЗДАЁТ\nПЕРЕВОД','1','0..N'),('employee','loan','РЕГИСТРИРУЕТ\nДОГОВОР','1','0..N')],
  {'card':(450,1400),'transfer':(1550,1400),'loan':(2700,1400),'account':(450,400),'employee':(1550,400),'schedule':(2700,400)},
  [(450,900),(950,1120),(1100,780),(1700,1030),(2700,900),(920,620),(1550,900),(2150,620)]))
 out.append(chen('A3_quality',[
  ('person','ЗАИНТЕРЕСОВАННОЕ ЛИЦО',['*Роль','Потребность']),
  ('req','ТРЕБОВАНИЕ',['*Код','Назначение','Функция']),
  ('criterion','КРИТЕРИЙ КАЧЕСТВА',['*Код критерия','Фактор','Метрика','Порог']),
  ('case','ОЦЕНОЧНЫЙ ЭЛЕМЕНТ\nПроверка',['*Код проверки','Вход и действия','Ожидаемый результат']),
  ('run','ЗАПУСК',['*Код запуска','Сборка и данные','Среда и время']),
  ('obs','НАБЛЮДЕНИЕ',['*Код наблюдения','Фактический результат','Вердикт']),
  ('evidence','СВИДЕТЕЛЬСТВО',['*Код','Путь','SHA-256'])],
  [('person','req','ПРЕДЪЯВЛЯЕТ','1..N','1..N'),('req','criterion','РАСКРЫВАЕТСЯ','1..N','1..N'),('criterion','case','ПРОВЕРЯЕТСЯ','1..N','1..N'),
   ('case','obs','ДАЁТ РЕЗУЛЬТАТ','1','0..N'),('run','obs','ОБЪЕДИНЯЕТ','1','1..N'),('evidence','obs','ПОДТВЕРЖДАЕТ','1','1..N')],
  {'person':(400,1400),'req':(1450,1400),'criterion':(2500,1400),'case':(2500,450),'run':(400,450),'obs':(1450,450),'evidence':(1450,900)},
  [(925,1400),(1975,1400),(2500,970),(1975,450),(925,450),(1450,690)]))
 return out

def logical(name,full,context=()):
 g=Graph(name,'LR',16)
 fixed={'bank_card':(250,900),'transfer':(850,900),'audit_event':(1450,900),'loan_schedule':(250,200),'loan':(850,250),'account':(1450,200),'employee':(1450,500)} if name=='A5_logical_products' else {}
 if fixed:g.body.append('graph [overlap=true,splines=true];')
 for id,title,fields in ENTITIES:
  if id not in full and id not in context:continue
  data=fields if id in full else [x for x in fields if x[2]=='PK']
  font=ImageFont.truetype(str(ARIAL),16)
  widths=[math.ceil(max(font.getlength(row[j]) for row in data)+24) for j in range(3)]
  rows=[]
  for row in data:
   cells=''.join(f'<TD WIDTH="{ww}" ALIGN="LEFT">{html.escape(t)}</TD>' for t,ww in zip(row,widths))
   rows.append(f'<TR><TD PORT="{row[0]}" CELLPADDING="0"><TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6"><TR>{cells}</TR></TABLE></TD></TR>')
  label=html.escape(title)+'<BR/>'+id+('<BR/>контекст А.4' if id in context else '')
  if id=='branch' and id in full:label+='<BR/>UQ: (city, address)'
  table=f'<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6"><TR><TD BGCOLOR="{BLUE}"><B>{label}</B></TD></TR>'+''.join(rows)+'</TABLE>'
  g.nodes.add(id);g.body.append(f'{id} [shape=plain,label=<{table}>];')
  if id in fixed:
   x,y=fixed[id];g.body.append(f'{id} [pos="{x/72},{y/72}!",pin=true];')
 for a,f,b,p in FK:
  if a in full and b in g.nodes:g.edge(f'{a}:{f}',f'{b}:{p}','',arrowhead='normal',arrowsize='.65')
 result=g.save()
 if fixed:result['engine']='neato'
 return result

def tree():
 s=Picture('B3_tree',1900,930)
 s.process(650,10,600,110,'0','Обеспечивать банковское обслуживание',29)
 xs=[15,395,775,1155,1535];s.line([(950,120),(950,175)]);s.line([(190,175),(1710,175)])
 for (code,title,children),x in zip(FUNCTIONS,xs):
  s.line([(x+175,175),(x+175,220)]);s.process(x,220,350,145,code,title,25)
  s.line([(x+175,365),(x+175,395),(x+15,395),(x+15,825)])
  for i,t in enumerate(children):
   y=420+i*140;s.line([(x+15,y+50),(x+45,y+50)]);s.filled(x+45,y,305,112,t,'white',24)
 s.text(950,895,'Каждый лист имеет вход, результат и проверку; порядок исполнения раскрывается процессной моделью.',24,1820)
 return s.save()

def states():
 s=Picture('V7_states',1800,980)
 data=[('Перевод','pending','completed','cancelled','Проведение / фиксация','Отмена'),('Карта','active','blocked','closed','Блокировка ↔ разблокировка','Закрытие'),('Договор','registered','closed',None,'Подтверждение закрытия','')]
 for i,(title,start,good,bad,goodlabel,badlabel) in enumerate(data):
  y=45+i*290;s.text(180,y+60,title,29,bold=True)
  s.filled(365,y+15,290,100,start,YELLOW,28,True);s.filled(1250,y+15,300,100,good,GREEN,28,True)
  s.line([(655,y+65),(1250,y+65)],True);s.text(950,y+22,goodlabel,24,550,bg=True)
  if bad:
   s.filled(1250,y+165,300,90,bad,BLUE,28,True);s.line([(655,y+90),(950,y+90),(950,y+210),(1250,y+210)],True)
   s.text(1040,y+260,badlabel,24,370,bg=True)
  if title=='Карта':
   s.line([(1250,y+95),(1100,y+95),(1100,y+135),(510,y+135),(510,y+115)],True)
   s.line([(1400,y+115),(1400,y+165)],True)
 s.text(900,940,'Отказ до фиксации не меняет состояние; неизвестный исход требует сверки. Даты доступности карты вычисляются отдельно от сохранённого статуса.',24,1720)
 return s.save()

def architecture():
 g=Graph('G1_architecture','TB',21)
 legend=('И1 — команда / результат; И2 — действие / ответ.\n'
         'И3 — данные / результат; факты для чтения.\n'
         'Д1 ↔ К6 по И3 — учётная запись / роль (только чтение).\n'
         'И4 — событие действия; единые правила аудита.\n'
         'И5 — контекст / запрос; И6 — результат действия.')
 g.body.append('graph [nodesep=.3, ranksep=.3, labelloc="b", labeljust="l", fontname="Arial", fontsize=20, label='+json.dumps(legend,ensure_ascii=False)+'];')
 def edge(a,b,text,**opts):g.edge(a,b,text.split(':',1)[0],**opts)
 for e,t in [('e1','Оператор'),('e2','Кредитный специалист'),('e3','Контролёр / руководитель'),('e4','Администратор')]:g.node(e,t)
 for id,t,*_ in COMPONENTS:g.node(id,t+'\n'+id,'box',YELLOW,style='rounded,filled')
 for d,t in [('Д1','Клиентский контекст'),('Д2','Карты'),('Д3','Переводы'),('Д4','Договоры и графики'),('Д5','Аудит')]:g.node(d,d+'\n'+t,'cylinder',GREEN)
 for e in ['e1','e2','e3','e4']:edge(e,'К6','И1: команда / результат',dir='both')
 for k in ['К1','К2','К3','К4','К5']:edge('К6',k,'И2: действие / ответ',dir='both')
 for k,ds in [('К1',['Д1']),('К2',['Д2']),('К3',['Д1','Д3']),('К4',['Д4'])]:
  for d in ds:edge(k,d,'И3: данные / результат',dir='both')
 edge('К6','Д1','И3: учётная запись / роль (чтение)',dir='both',constraint='false')
 for d in ['Д1','Д2','Д3','Д4','Д5']:edge(d,'К5','И3: факты для чтения')
 for k in ['К2','К3','К4']:edge('К1',k,'И5: контекст / запрос',dir='both')
 for k in ['К1','К2','К3','К4']:edge(k,'К5','И6: результат действия')
 for k in ['К1','К2','К3','К4']:edge(k,'Д5','И4: событие действия')
 edge('К6','Д5','И4: единые правила аудита')
 return g.save()

def general_functioning():
 g=Graph('G2_functioning','TB',24)
 g.body.append('graph [nodesep=.2, ranksep=.2];')
 nodes=[('e','Сотрудник: обращение',BLUE),('ctx','К1\nЕдиный клиентский контекст',YELLOW),('trust','К6\nРоль, основание, ключ',YELLOW),('card','К2\nКарта и доступность',YELLOW),('tr','К3\nСогласованный перевод',YELLOW),('loan','К4\nДоговор и план',YELLOW),('control','К5\nДокумент и сверка',YELLOW),('done','Проверенный результат\nдля пользователя',GREEN)]
 for id,t,c in nodes:g.node(id,t,'box',c,style='rounded,filled')
 for a,b,t in [('e','trust','Команда и сеанс'),('trust','ctx','Проверенные полномочия'),('ctx','card','Карточный маршрут'),('ctx','tr','Платёжный маршрут'),('ctx','loan','Кредитный маршрут'),('ctx','control','Карточка клиента'),('card','control','Состояние'),('tr','control','Подтверждённый факт'),('loan','control','Условия и план'),('control','done','Документ; актуальность')]:g.edge(a,b,wrap(t,12))
 return g.save()

def reasoning():
 s=Picture('G3_reasoning',2800,1330)
 titles=['Проблема','Гипотеза / решение','Функция','Компонент → модуль','Проверка','Мера результата']
 xs=[20,470,920,1270,1830,2280];ww=[400,400,300,510,400,480]
 for x,w,t in zip(xs,ww,titles):s.filled(x,15,w,80,t,BLUE,36)
 rows=[['ПР1\nРазрозненные реквизиты','Г1\nЕдиный контекст\nи проверки до записи','F1, F2','К1, К2, К6\nМ01–М03, М10, М11','И01–И05, И23','0 повторных переносов;\nверные связанные карточки'],
 ['ПР2\nПовтор и гонка списаний','Г2\nОдно атомарное\nпроведение с ключом','F3','К3, К6\nМ04, М05, М10, М11','И07–И12','0 частичных операций;\nсумма средств сохранена'],
 ['ПР3\nОшибки плана кредита','Г3\nЕдиная формула\nи точный остаток','F4','К4, К6\nМ06, М07, М10, М11','И13–И16, И23','Сумма долей = principal;\nвсе даты и проценты верны'],
 ['ПР4\nНесогласованные сводки','Г4\nОбщая модель\nи явный период','F5','К5, К6\nМ08–М11','И17, И19, И23','Верный эталон; p95;\nтри задачи без SQL']]
 for j,row in enumerate(rows):
  y=150+j*280
  for i,(x,w,t) in enumerate(zip(xs,ww,row)):
   s.filled(x,y,w,185,t,GREEN if i==5 else YELLOW,36,True)
   if i<5:s.line([(x+w,y+92),(xs[i+1],y+92)],True)
 s.text(1400,1290,'Г1–Г4 обеспечивают общую Г0. Польза организатору проверяется отдельно И24/И25: 30 пар А/Б и полный труд.',36,2700)
 return s.save()

def deployment():
 s=Picture('D1_deployment',1800,1000)
 s.box(15,20,1770,850);s.text(900,60,'Среда банка — техническое воплощение облика',29,bold=True)
 s.filled(50,190,310,170,'Рабочие места\nМ09: формы и отчёты\nБраузер; HTTPS',BLUE,27)
 s.box(520,130,1190,470);s.text(1115,170,'Сервер; Docker Compose; внутренняя сеть',27)
 s.filled(580,260,430,200,'app: Python, FastAPI\nМ01–М10; формы М09\nМ05: координатор транзакции\nМаршрутизация и права',YELLOW,25)
 s.filled(1190,260,450,200,'db: PostgreSQL\nД1–Д5; М05: функция\nМ11: аудит; ограничения\nи представления',GREEN,25)
 s.line([(360,270),(580,330)],True);s.text(465,230,'И1 / И2\nHTTPS JSON',24,205,bg=True)
 s.line([(1010,350),(1190,350)],True);s.text(1100,290,'И3 / И4\nSQL',24,175,bg=True)
 s.filled(1190,510,450,65,'Постоянный том данных',GREEN,25);s.line([(1415,460),(1415,510)],True)
 s.filled(70,700,650,120,'Отдельный испытательный контур\nФикстуры; две сессии; нагрузка; свидетельства',BLUE,25)
 s.filled(1120,700,560,120,'Резервные копии и восстановление\nв отдельную БД',GREEN,25)
 s.line([(1415,575),(1415,700)],True)
 s.text(900,940,'Секреты вне кода; миграции до старта; БД недоступна рабочим местам. И1–И6 уточняются контрактами приложения И.',24,1720)
 return s.save()

def realization():
 s=Picture('D2_realization',2700,1550)
 for x,w,t in [(30,540,'Архитектурный компонент'),(770,1000,'Разрабатываемые модули'),(1950,700,'Технические средства и данные')]:s.filled(x,10,w,85,t,BLUE,35)
 details=[('К1','Клиентский контекст','М01 Клиенты и справочники\nМ02 Счета','Формы; API; branch, client,\naccount, employee'),('К2','Карточное обслуживание','М03 Карты','Форма карты; правила срока;\nbank_card'),('К3','Проведение переводов','М04 Подготовка перевода\nМ05 Транзакционное проведение','Форма перевода; post_transfer;\naccount, transfer'),('К4','Кредитный учёт','М06 Кредитные договоры\nМ07 Расчёт графика','Форма договора; build_schedule;\nloan, loan_schedule'),('К5','Контроль результатов','М08 Запросы и сверка\nМ09 Пользовательские сценарии','VIEW; SQL Q1–Q8;\nкарточки, выписка, сводка'),('К6','Доверие к действиям','М10 Полномочия и контекст\nМ11 Аудит изменений','Политики ролей; триггеры;\nemployee; audit_event')]
 for i,(code,title,modules,tech) in enumerate(details):
  y=150+i*215;s.filled(30,y,540,150,code+'\n'+title,YELLOW,35,True);s.filled(770,y,1000,150,modules,YELLOW,35,True);s.filled(1950,y,700,150,tech,GREEN,35,True)
  s.line([(570,y+75),(770,y+75)],True);s.line([(1770,y+75),(1950,y+75)],True)
 s.text(1350,1505,'Для каждого М-модуля заданы вход, выход, правило, ошибки и испытание; HTTP и SQL реализуют интерфейсы облика.',35,2610)
 return s.save()

def renamed_primitive(fn,old,new,replacements):
 item=fn();p=FIG/(old+'.svg');text=p.read_text(encoding='utf-8')
 for a,b in replacements:text=text.replace(a,b)
 dest=FIG/(new+'.svg');dest.write_text(text,encoding='utf-8');p.unlink()
 item.update(name=new,source='svg',sha256_svg=hashlib.sha256(dest.read_bytes()).hexdigest());return item

def schedule_algorithm():
 s=Picture('D4_schedule',1600,1110)
 s.box(80,20,580,65,'Начало',26,'terminal');s.box(80,130,580,95,'principal, annual_rate,\nissued_on, due_on, даты',26,'io')
 s.box(160,290,420,130,'Ввод\nкорректен?',26,'diamond')
 s.box(80,485,580,95,'Вычислить базовую долю\nв целых копейках',26)
 s.box(80,645,580,105,'Для каждой даты: проценты HALF_UP;\nпоследней доле — остаток',25)
 s.box(160,825,420,130,'Сумма и сроки\nсогласованы?',26,'diamond')
 for a,b in [(85,130),(225,290),(420,485),(580,645),(750,825)]:s.line([(370,a),(370,b)],True)
 s.text(410,455,'Да',24,bg=True)
 s.circle(790,355,22,'Б');s.line([(580,355),(768,355)],True);s.text(675,323,'Нет',24,bg=True)
 s.circle(80,890,22,'Б');s.line([(160,890),(102,890)],True);s.text(120,850,'Нет',24,bg=True)
 s.circle(1200,355,22,'Б');s.box(920,475,580,120,'Отклонить; договор\nи строки не записывать',26)
 s.line([(1200,377),(1200,475)],True);s.box(1020,655,360,65,'Отказ',26,'terminal');s.line([(1200,595),(1200,655)],True)
 s.box(920,825,580,130,'Вернуть полный план\nдля атомарной записи М06',26,'io');s.line([(580,890),(920,890)],True);s.text(750,855,'Да',24,bg=True)
 s.box(1020,995,360,65,'Конец',26,'terminal');s.line([(1200,955),(1200,995)],True)
 s.text(800,1090,'Проценты: долг × ставка/100 × дни/365. Пара соединителей Б ведёт к общему отказу.',23,1510)
 return s.save()

def sequence():
 s=Picture('D6_sequence',2100,1120)
 xs=[180,650,1190,1770];titles=['Оператор','М09\nИнтерфейс и запрос','М04 / М05 / М10\nСервис и права','М05: функция БД\nМ11: аудит']
 for x,t in zip(xs,titles):s.filled(x-155,15,310,100,t,BLUE,26);s.line([(x,115),(x,1025)],dash=True)
 exchanges=[(180,650,180,'1. Ключ, реквизиты, команда'),(650,1190,280,'2. Сеанс и transfer_id; проверка М10'),(1190,1770,380,'3. BEGIN; вызов post_transfer'),(1770,1770,500,'4. Блокировки; проверки; остатки; статус; аудит'),(1770,1190,650,'5. Подготовленный результат либо ошибка'),(1190,1770,760,'6. COMMIT; известная ошибка — откат'),(1190,650,890,'7. Подтверждённый итог / исход неизвестен'),(650,180,1000,'8. ID, статус; при потере ответа — сверка')]
 for a,b,y,t in exchanges:
  if a==b:
   s.line([(a,y),(a+260,y),(a+260,y+70),(a,y+70)],True);s.text(1500,y+10,t,26,490,bg=True)
  else:s.line([(a,y),(b,y)],True);s.text((a+b)/2,y-32,t,26,abs(a-b)-35,bg=True)
 s.text(1050,1080,'Потеря подтверждения COMMIT: GET прежнего ID либо повтор с прежним ключом; отсутствие ответа не доказывает откат.',26,2010)
 return s.save()

def quality_decision():
 s=Picture('E1_quality',2400,1100)
 blocks=[(20,90,'Интерес организатора\nи требования назначения',BLUE),(620,90,'Критерии качества:\nЦП1–ЦП4; КР1–КР6',YELLOW),(1220,90,'Проверка И01–И25:\nданные, действия, эталон',YELLOW),(1820,90,'Запуск:\nсборка, среда, исполнитель',BLUE),(1820,670,'Наблюдение:\nрезультат, время, весь труд',YELLOW),(1220,670,'Свидетельства:\nснимки, журналы А/Б, SHA-256',GREEN),(620,670,'Сравнение с нормой\nпо каждому требованию',YELLOW),(20,670,'Решение по назначению:\nпринять / исправить /\nнедостаточно свидетельств',GREEN)]
 for x,y,t,c in blocks:s.filled(x,y,540,225,t,c,29,True)
 for a,b in [(0,1),(1,2),(2,3)]:s.line([(blocks[a][0]+540,202),(blocks[b][0],202)],True)
 s.line([(2090,315),(2090,670)],True);s.text(2210,490,'Измерение',29,330,bg=True)
 for a,b in [(4,5),(5,6),(6,7)]:s.line([(blocks[a][0],782),(blocks[b][0]+540,782)],True)
 s.line([(890,315),(890,670)],True);s.text(1020,490,'Заранее\nзаданный порог',29,320,bg=True)
 s.text(1200,1020,'Приёмка: все нормы и 30 сопоставимых обращений А/Б. Критический дефект исключает успех; без базы А эффект неизвестен.',29,2300)
 return s.save()

def main():
 validate_model()
 catalog=declarative()+[logical('A4_logical_people',{'branch','client','account','employee'}),logical('A5_logical_products',{'bank_card','transfer','loan','loan_schedule','audit_event'},{'account','employee'}),tree()]+dfd_figures.all_figures()+process_figures.all_processes()+[states(),architecture(),general_functioning(),reasoning(),deployment(),realization(),renamed_primitive(primitive.algorithm,'G1_posting','D3_transfer',[('order_id','transfer_id'),('поручение','перевод'),('поручения','перевода'),('Создать transfer;','Установить completed;'),('завершить перевод;','записать finished_at;'),('записать аудит','сохранить аудит')]),schedule_algorithm(),renamed_primitive(primitive.concurrency,'G3_concurrency','D5_concurrency',[]),sequence(),quality_decision()]+additional_figures.all_additional()
 by_name={x['name']:x for x in catalog}
 assert len(by_name)==len(catalog)
 catalog=[by_name[f['name']] for f in FIGURES]
 for item in catalog:
  item.update(paper=BY_NAME[item['name']]['paper'],caption=BY_NAME[item['name']]['caption']);item.setdefault('source','svg')
 assert len(catalog)==len(FIGURES)==36
 (SRC/'figures_manifest.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
 print_layout={f['name']:{key:f[key] for key in ('paper','orientation','max_width_mm','max_height_mm')} for f in FIGURES}
 (SRC/'print_layout.json').write_text(json.dumps(print_layout,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'Created {len(catalog)} diagram sources')
if __name__=='__main__':main()
