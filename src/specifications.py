"""Поля и контракты технического проекта; реализация банковского ПО не имитируется."""
import json
from project_model import ENTITIES,ROOT

MEANINGS={
 'branch': ['Идентификатор отделения','Уникальный код отделения','Город','Адрес; пара город–адрес уникальна'],
 'client': ['Идентификатор клиента','Фамилия, имя и отчество','Уникальный телефон','Уникальная электронная почта','Момент регистрации'],
 'account': ['Идентификатор счёта','Уникальный номер: ровно 20 цифр','Единственный владелец','Обслуживающее отделение','Дата открытия','active либо inactive','Подтверждённый остаток на начало текущей книги','Текущий остаток; изменяется только проведением'],
 'employee': ['Идентификатор сотрудника','Отделение сотрудника','Уникальное имя входа','Хеш с солью и параметрами; не выдаётся в API','Фамилия, имя и отчество','operator / credit / controller / admin','Разрешён ли доступ сейчас'],
 'bank_card': ['Идентификатор карты','Уникальный номер: ровно 16 цифр; в списках маскируется','Обслуживаемый счёт','Первый допустимый день','Последний допустимый день; позже issued_on','active / blocked / closed','Сотрудник, зарегистрировавший карту'],
 'transfer': ['Идентификатор распоряжения','Счёт списания','Другой счёт зачисления','Положительная сумма; предел команды 1 000 000,00 руб.','Момент инициирования распоряжения','pending / completed / cancelled','Уникальный ключ создания команды','Автор из проверенного сеанса','Момент completed/cancelled; NULL только при pending'],
 'loan': ['Внутренний идентификатор договора','Уникальный номер исходного утверждённого договора; неизменяемый contract_ref','Связанный активный счёт','Положительная основная сумма','Годовая ставка от 0,00 до 999,99 %','Дата начала договорного периода','Последняя дата утверждённого плана','registered / closed','Сотрудник первоначальной регистрации','Основание кредитной службы; непустое только для closed'],
 'loan_schedule': ['Договор; первая часть составного PK','Номер от 1 до N; вторая часть PK','Позже loan.issued_on; даты возрастают, последняя равна loan.due_on','Положительная часть основного долга','Неотрицательная процентная часть; HALF_UP'],
 'audit_event': ['Идентификатор события','Автор из доверенного контекста','Имя изменённого отношения','Идентификатор объекта без универсального FK','create / update / post / cancel / close','Момент события с часовым поясом','Ключ команды; объединяет события одной операции','Снимок до; NULL для создания; без секретов','Снимок после; обязательный для изменения; без секретов'],
}

# Смысл границ уточняется до конкретного синтаксиса, а не заменяется названием REST.
CONTRACTS=[
 ('Т01','М09 → М10','HTTPS; JSON UTF-8; защищённый сеанс','POST /api/v1/transfers: from_account_id:int, to_account_id:int, amount:string, request_key:UUID; POST /transfers/{id}/post и GET /transfers/{id}: ID в пути','201/200 TransferView / PostingResult либо Error; GET читает прежний исход с проверкой прав; actor_id не принимается от клиента'),
 ('Т02','М10 → М04','Python 3.12; типизированный вызов','dispatch(command, ctx:ActorContext) → TransferView / подготовленный ID; prepare и resolve_repeat; ctx: employee_id, role, request_id','BT001/002/004/005; проверка роли и активности до записи'),
 ('Т03','М04 / М09 → координатор М05','Python; общий доверенный контекст','post(transfer_id:int, ctx:ActorContext) → PostingResult; положительный ID','Исход completed либо доменный отказ; повтор возвращает тот же факт'),
 ('Т04','Координатор М05 → серверная функция М05','psycopg 3; параметризованный SQL; одна транзакция','SELECT post_transfer(%s::integer, %s::integer, %s::uuid); параметры: transfer_id, actor_id, request_id','jsonb либо SQLSTATE BT001…BT005; BEGIN/COMMIT у координатора. Ключ аудита — из заблокированного transfer; request_id — корреляция вызова'),
 ('Т05','Серверная операция → М11','SQL; триггер в текущей транзакции','Предметная строка OLD/NEW и transaction-local actor_id / request_key; обе величины задаёт доверенный сервис','Строки audit_event; при сбое аудита откат всей операции'),
 ('Т06','М05 / М11 → Д1, Д3, Д5','SQL; блокировки строк и ограничения','Парные balance; transfer.status / finished_at; аудит; всё под одним COMMIT','Конечный факт доступен после фиксации; нет произвольного UPDATE от формы'),
 ('Т07','Серверная функция → координатор М05','SQL jsonb либо исключение SQLSTATE','{transfer_id:int,status:"completed",finished_at:RFC3339,request_key:UUID}; код ошибки вне успешного JSON','40P01/40001: до трёх попыток транзакции с прежним ключом; известная ошибка до фиксации → ROLLBACK. Потеря связи при COMMIT → сверка сохранённого состояния'),
 ('Т08','Координатор М05 → М09','Python DTO → HTTPS JSON UTF-8','HTTP 200; PostingResult и request_id; сериализация денег строками, дат ISO 8601','Успех после подтверждённого COMMIT. Потеря ответа: GET состояния либо повтор с прежним ключом/ID; до сверки исход неизвестен вызывающему'),
 ('Т09','М06 → М07','Python; чистый детерминированный вызов','build(principal:Decimal, rate:Decimal, issued_on:date, dates:list[date]) → list[ScheduleItem]','Основные части, даты, проценты; ошибка BT006 до записи'),
 ('Т10','М01–М04, М06 → контекст К1','Python; разрешённое чтение; для денег чтение внутри текущей транзакции','AccountContext: id, client_id, branch_id, status, balance; ClientContext: id, разрешённые реквизиты','Контекст для показа не заменяет повторную проверку под блокировкой М05'),
 ('Т11','Профильные модули → М08/М09','Python Outcome DTO; чтение подтверждённого состояния','kind, request_id, типизированные details; entity_id — у предметного объекта; status — у счёта, карты, перевода или договора','ResultPresenter.render; документ не изменяет исходный факт; доступ проверяется заново'),
]

ERRORS=[
 ('AUTH','Нет действующего сеанса','401','Предметные записи не изменены'),
 ('BT001','Объект не найден','404','Не создавать заменяющий объект автоматически'),
 ('BT002','Нет права / сотрудник отключён','403','Отказ до предметной записи'),
 ('BT003','Недостаточно средств','409','Полный откат; перевод остаётся pending'),
 ('BT004','Недопустимые поля, состояние или переход','422 / 409','422 для формы данных; 409 для конфликта текущего состояния'),
 ('BT005','Ключ перевода: иные параметры/автор; contract_ref: иные условия','409','Конфликт без нового перевода или договора'),
 ('BT006','Невозможный или несогласованный график','422','Не сохранять часть договора или плана'),
 ('BT099','Исчерпание повторов / недоступность инфраструктуры','503','Нет подтверждённого успеха; безопасно запросить прежний результат'),
 ('INTERNAL','Непредвиденная ошибка реализации','500','request_id для диагностики; внутренние SQL и секреты не выдавать'),
]

def field_rows():
 rows=[]
 for name,title,fields in ENTITIES:
  assert len(fields)==len(MEANINGS[name]),name
  rows.extend((name+'.'+f,t+'; '+flags,meaning) for (f,t,flags),meaning in zip(fields,MEANINGS[name]))
 return rows

def write_annex(w,app,table):
 app('И','Словарь данных и спецификации интерфейсов',first=True)
 w.p('Словарь уточняет атрибуты рисунков А.4–А.5. Целые ключи неизменяемы; внешние ключи проверяются СУБД; удаление связанных строк запрещено. Денежные поля передаются JSON-строками с двумя десятичными знаками и хранятся точно. События передаются как RFC 3339 с явным смещением; date не содержит времени.')
 for name,title,fields in ENTITIES:
  rows=[(f,t+'; '+flags,m) for (f,t,flags),m in zip(fields,MEANINGS[name])]
  table(w,title+' '+name,['Поле','Тип и ограничения','Смысл'],rows,[42,46,77])
 w.p('Поле opening_balance задаётся при вводе подтверждённого начального среза, а при обычном открытии нового счёта равно 0,00. Изменение balance вне проведения запрещено. Корректировки, комиссии, валютный обмен и пополнения наличными в данный контур не входят. Общая сумма остатков сохраняется для всех допустимых переводов текущей книги. Для события loan_schedule поле entity_id содержит loan_id, а payment_no сохраняется в old/new и уточняет строку составного объекта.')
 table(w,'Детальные контракты связей',['ID и граница','Синтаксис и вход','Результат и семантика'],[(i+' '+b,p+'; '+inp,out) for i,b,p,inp,out in CONTRACTS],[35,73,57])
 table(w,'Единая классификация отказов',['Код','Условие','HTTP','Правило'],ERRORS,[25,39,21,80])
 w.p('Все сетевые команды используют префикс /api/v1 и Content-Type: application/json; charset=utf-8. POST /sessions проверяет учётные данные и создаёт сеанс; остальные команды требуют проверенного сервером сеанса. Поля вне схемы отклоняются, числовые ID должны быть положительными. Денежная строка допускает только точку и ровно две цифры после неё, без разделителей групп. Автор вычисляется из сеанса; пароль, cookie и хеш не записываются в аудит. Для всех ответов формируется request_id.')
 for title,example in EXAMPLES:
  w.p(title,keep=True,before=6)
  p=w.p(json.dumps(example,ensure_ascii=False,indent=2),align=0,size=12,indent=0,after=6)
  p.paragraph_format.line_spacing=1;p.paragraph_format.keep_together=True
 w.p('Файл contracts/openapi.json задаёт сетевые схемы ключевых денежных и кредитных команд в OpenAPI 3.1 [15]. Остальные команды приложения Д используют общие правила типов и конверта ответа. Для внутрипроцессных Т02/Т03/Т09–Т11 определены Python-типы и результаты, для Т04–Т07 — SQL-вызовы и условия транзакции. Поля отношений определены настоящим словарём.')

EXAMPLES=[
 ('Создание распоряжения POST /api/v1/transfers',{'from_account_id':101,'to_account_id':102,'amount':'2500.00','request_key':'11111111-1111-4111-8111-111111111111'}),
 ('Ответ проведения POST /api/v1/transfers/501/post после COMMIT',{'transfer_id':501,'status':'completed','finished_at':'2026-11-01T10:30:00+03:00','request_key':'11111111-1111-4111-8111-111111111111','request_id':'22222222-2222-4222-8222-222222222222'}),
 ('Отказ HTTP 409 без предметного изменения',{'error':{'code':'BT003','message':'Недостаточно средств'},'request_id':'22222222-2222-4222-8222-222222222222'}),
 ('Регистрация утверждённого договора POST /api/v1/loans',{'contract_ref':'КД-2026-0001','account_id':101,'principal':'120000.00','annual_rate':'12.00','issued_on':'2026-01-01','due_on':'2026-04-01','payment_dates':['2026-02-01','2026-03-01','2026-04-01']}),
]

def write_openapi():
 money={'type':'string','pattern':r'^[0-9]{1,12}\.[0-9]{2}$'}
 ident={'type':'integer','minimum':1,'maximum':2147483647}
 uuid={'type':'string','format':'uuid'}
 contract_ref={'type':'string','minLength':1,'maxLength':100,'pattern':r'\S','description':'Номер утверждённого договора в формате банка; крайние пробелы удаляются до сравнения. Номер сохраняется неизменным.'}
 def obj(props,required=None):return {'type':'object','additionalProperties':False,'properties':props,'required':required or list(props)}
 schemas={
  'TransferCommand':obj({'from_account_id':ident,'to_account_id':ident,'amount':money,'request_key':uuid}),
  'TransferView':obj({'transfer_id':ident,'status':{'enum':['pending','completed','cancelled']},'request_key':uuid,'request_id':uuid}),
  'PostingResult':obj({'transfer_id':ident,'status':{'const':'completed'},'finished_at':{'type':'string','format':'date-time'},'request_key':uuid,'request_id':uuid}),
  'LoanCommand':obj({'contract_ref':contract_ref,'account_id':ident,'principal':money,'annual_rate':{'type':'string','pattern':r'^[0-9]{1,3}\.[0-9]{2}$'},'issued_on':{'type':'string','format':'date'},'due_on':{'type':'string','format':'date'},'payment_dates':{'type':'array','minItems':1,'uniqueItems':True,'items':{'type':'string','format':'date'}}}),
  'ScheduleItem':obj({'payment_no':ident,'due_on':{'type':'string','format':'date'},'principal_part':money,'interest_part':money}),
  'LoanView':obj({'loan_id':ident,'contract_ref':contract_ref,'created_by':ident,'status':{'enum':['registered','closed']},'schedule':{'type':'array','items':{'$ref':'#/components/schemas/ScheduleItem'}},'request_id':uuid}),
  'CloseCommand':obj({'close_ref':{'type':'string','minLength':1,'maxLength':100}}),
  'Error':obj({'error':obj({'code':{'type':'string'},'message':{'type':'string'}}),'request_id':uuid}),
 }
 def response(name):return {'description':'Результат по контракту','content':{'application/json':{'schema':{'$ref':'#/components/schemas/'+name}}}}
 def op(command,result,created=False):
  x={'responses':{'201' if created else '200':response(result),**{s:response('Error') for s in ['401','403','404','409','422','500','503']}}}
  if command:x['requestBody']={'required':True,'content':{'application/json':{'schema':{'$ref':'#/components/schemas/'+command}}}}
  if created:x['responses']['200']=response(result)
  return x
 paths={'/transfers':{'post':op('TransferCommand','TransferView',True)},'/transfers/{id}':{'get':op(None,'TransferView')},'/transfers/{id}/post':{'post':op(None,'PostingResult')},'/loans':{'post':op('LoanCommand','LoanView',True)},'/loans/{id}/close':{'post':op('CloseCommand','LoanView')}}
 paths['/transfers/{id}']['get']['description']='Чтение подтверждённого состояния с проверкой сеанса и права на объект. После потери ответа completed означает прежний успех; pending допускает повтор проведения того же ID. Недоступность чтения не доказывает откат.'
 paths['/loans']['post']['description']='contract_ref однозначно обозначает исходный утверждённый договор. Новый договор: 201. Совпавший повтор ссылки, счёта и всех условий: 200 с прежними loan_id, автором, текущим состоянием и планом; повторного аудита создания нет. Иные условия с той же ссылкой: 409 BT005. Первая дата платежа строго позже issued_on; даты возрастают, последняя равна due_on. При потере ответа повторяется исходная команда с прежним contract_ref.'
 for path,methods in paths.items():
  if '{id}' in path:methods['parameters']=[{'name':'id','in':'path','required':True,'schema':ident}]
 data={'openapi':'3.1.0','info':{'title':'Банковская система — ключевые контракты','version':'1.0.0','description':'Проектная спецификация. Семантические ограничения и транзакции описаны в записке; сервис ещё не реализован.'},'servers':[{'url':'https://bank.example.invalid/api/v1'}],'security':[{'session':[]}],'paths':paths,'components':{'securitySchemes':{'session':{'type':'apiKey','in':'cookie','name':'session'}},'schemas':schemas}}
 target=ROOT/'contracts';target.mkdir(exist_ok=True)
 (target/'openapi.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return data

if __name__=='__main__':print('Fields:',len(field_rows()),'; OpenAPI:',write_openapi()['openapi'])
