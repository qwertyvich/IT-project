"""Проектные задания модулей: данные для документации, не реализация и не полная РКД.

signature печатается в существующей таблице Д; task экспортируется в JSON.
Типы отношений и предельные длины заданы словарём И. Политики канонизации
контактов и реквизитов применяются до проверок уникальности согласно общим
правилам проекта; здесь альтернативная нормализация не вводится.
"""

_CTX = {
    'employee_id': 'int > 0, только из проверенного сервером сеанса',
    'role': 'operator | credit | controller | admin; актуальное право проверяет М10',
    'request_id': 'UUID корреляции; не заменяет request_key учётной команды',
}


_FORMAT = 'В Python деньги — Decimal, даты — date, моменты — timezone-aware datetime. В JSON деньги — строки с двумя знаками, даты ISO 8601, моменты RFC 3339 со смещением.'
_VIEW = 'View содержит только разрешённые поля соответствующего отношения из И; password/password_hash, cookie и внутренний SQL исключены. Полный PAN не передаётся в отображаемый View: только последние четыре цифры.'


DETAILS = {
    'М01': {
        'signature': 'ClientService.save(id?,ClientInput,ctx)→ClientView; ReferenceService.save(kind,id?,data,ctx)→ReferenceView',
        'task': {
            'signature': [
                'ClientService.save(id:int|None, data:ClientInput, ctx:ActorContext) -> ClientView',
                'ReferenceService.save(kind:branch|employee, id:int|None, data:BranchInput|EmployeeInput, ctx:ActorContext) -> ReferenceView',
            ],
            'inputs': {
                'ctx': _CTX,
                'id': 'None означает создание; положительный существующий ID означает PATCH.',
                'ClientInput': {'full_name': 'непустая str, до 150', 'phone': 'непустая str, до 20', 'email': 'непустая str, до 150'},
                'BranchInput': {'branch_code': 'непустая str, до 10', 'city': 'непустая str, до 100', 'address': 'непустая str, до 200'},
                'EmployeeInput': {
                    'branch_id': 'int > 0', 'login': 'непустая str, до 80', 'full_name': 'непустая str, до 150',
                    'role_code': 'operator | credit | controller | admin', 'is_active': 'bool',
                    'password': 'непустая str, write_only; обязательна только при create; передаётся М10 для хеширования',
                },
                'patch_semantics': 'При create обязательны все поля своего Input. PATCH меняет только переданные разрешённые поля; отсутствующее поле сохраняет значение, null для NN запрещён. Пустой PATCH, лишние поля и изменение PK/registered_at отклоняются. password и password_hash запрещены в обычном PATCH.',
                'canonicalization': 'Применить общую политику канонизации проекта до проверки длины/формата/уникальности; не изобретать отдельные правила.',
            },
            'preconditions': [
                'М10 подтверждает активность и право: clients.save — operator, references.save — admin.',
                'Для update объект существует; EmployeeInput.branch_id ссылается на существующее отделение.',
                'После канонизации уникальны client.phone/email, branch.branch_code и пара city/address, employee.login; ограничение СУБД повторяет проверку при конкуренции.',
                'Внешний JSON не принимает password_hash. При create employee М10 получает password и возвращает внутренний хеш с солью и параметрами; пароль не сохраняется.',
            ],
            'postconditions': {
                'returns': 'ClientView/BranchView/EmployeeView: разрешённые поля соответствующей строки И, включая исходный ID; EmployeeView без password/password_hash.',
                'effects': [
                    'Создание выдаёт новый ID; registered_at клиента задаётся сервером. PATCH сохраняет неизменяемые поля.',
                    'Предметная запись и audit_event фиксируются одной транзакцией; автор — ctx.employee_id. При отказе нет частичного изменения.',
                    'Отключение сотрудника запрещает последующие действия и через прежний сеанс; М10 читает актуальные активность и роль.',
                    _VIEW,
                ],
            },
            'errors': {'AUTH/401': 'нет сеанса', 'BT001/404': 'не найден объект/отделение', 'BT002/403': 'нет права или сотрудник отключён', 'BT004/422': 'форма, тип, предел длины, null/лишнее/неизменяемое поле', 'BT004/409': 'конфликт уникальности', 'BT099/503': 'нет подтверждённого сохранения; не показывать успех'},
            'verificationIDs': ['И01', 'И03', 'И12', 'И18'],
        },
    },
    'М02': {
        'signature': 'open(client_id,branch_id,account_number,ctx)→AccountView; context(id,ctx)→AccountContext; set_status(id,inactive,ctx)→AccountView',
        'task': {
            'signature': ['AccountService.open(client_id:int, branch_id:int, account_number:str, ctx:ActorContext) -> AccountView', 'AccountService.context(id:int, ctx:ActorContext) -> AccountContext', 'AccountService.set_status(id:int, target:inactive, ctx:ActorContext) -> AccountView'],
            'inputs': {'ctx': _CTX, 'client_id/branch_id/id': 'int > 0, существующие объекты', 'account_number': 'str из ровно 20 цифр после общей канонизации', 'target': 'только inactive; иные состояния или поля баланса не принимаются'},
            'preconditions': ['М10 подтверждает активность и право: открытие/отключение — operator; чтение контекста — разрешённому пользователю.', 'Номер уникален; клиент и отделение существуют. Поля вне сигнатуры запрещены.', 'Отключение проверяет balance=0 под блокировкой строки счёта в той же транзакции, чтобы исключить гонку с переводом.'],
            'postconditions': {
                'returns': {'AccountView': 'account_id, account_number, client_id, branch_id, opened_on, status, opening_balance:Decimal, balance:Decimal', 'AccountContext': 'id, client_id, branch_id, status, balance:Decimal, как Т10'},
                'effects': ['Обычное открытие создаёт active, opened_on задаётся серверной датой, opening_balance=balance=0,00.', 'Подтверждённый ненулевой начальный срез вводит только процедура переноса; обычный open его не принимает.', 'set_status сохраняет inactive при нулевом остатке; повтор inactive не меняет денег. Прямые изменения balance/opening_balance и владельца существующего счёта не допускаются.', 'Сохранение и аудит атомарны; context не пишет данные и не заменяет повторную проверку М05 под блокировкой.', _FORMAT],
            },
            'errors': {'AUTH/401': 'нет сеанса', 'BT001/404': 'не найден счёт/клиент/отделение', 'BT002/403': 'нет права или неактивный сотрудник', 'BT004/422': 'недопустимый ID, номер или поле', 'BT004/409': 'дубль номера либо отключение с ненулевым остатком', 'BT099/503': 'нет подтверждённого сохранения'},
            'verificationIDs': ['И02', 'И07', 'И12', 'И18'],
        },
    },
    'М03': {
        'signature': 'register(account_id,card_number,issued_on,expires_on,ctx)→CardView; change_status(id,target,ctx)→CardView; availability(id,date,ctx)→bool',
        'task': {
            'signature': ['CardService.register(account_id:int, card_number:str, issued_on:date, expires_on:date, ctx:ActorContext) -> CardView', 'CardService.change_status(id:int, target:active|blocked|closed, ctx:ActorContext) -> CardView', 'CardService.availability(id:int, date:date, ctx:ActorContext) -> bool'],
            'inputs': {'ctx': _CTX, 'account_id/id': 'int > 0', 'card_number': 'str из ровно 16 цифр; уникальна', 'issued_on/expires_on/date': 'date; в JSON YYYY-MM-DD', 'target': 'active | blocked | closed'},
            'preconditions': ['М10 подтверждает активность и право на карточное действие; запись выполняет operator.', 'Для register счёт существует и active; expires_on строго позже issued_on. Лишние поля, включая issued_by извне, запрещены.', 'Переход состояния проверяется по сохранённому состоянию под блокировкой. availability читает и inactive-счёт: в этом случае возвращает false, не ошибку проверки активности.'],
            'postconditions': {
                'returns': 'CardView: card_id, account_id, issued_on, expires_on, status, issued_by; вместо полного card_number — маска с последними четырьмя цифрами.',
                'effects': ['Регистрация создаёт active; issued_by=ctx.employee_id. Карта и аудит сохраняются атомарно.', 'Разрешены active→blocked, blocked→active, active/blocked→closed; closed окончателен. Повтор текущего состояния не создаёт новую смену состояния.', 'availability возвращает true ровно при card.status=active, account.status=active и issued_on≤date≤expires_on. Проверка вычисляется, не меняя состояние и не создавая операцию оплаты.', 'Номер, счёт и даты зарегистрированной карты не изменяются методом change_status; отказ не меняет строку.', _VIEW],
            },
            'errors': {'AUTH/401': 'нет сеанса', 'BT001/404': 'нет карты/счёта', 'BT002/403': 'нет права или сотрудник отключён', 'BT004/422': 'номер, дата, ID или лишнее поле неверны', 'BT004/409': 'номер занят, счёт inactive или переход из closed запрещён', 'BT099/503': 'нет подтверждённого сохранения'},
            'verificationIDs': ['И04', 'И05', 'И18', 'И23'],
        },
    },
    'М08': {
        'signature': 'StatementQuery.execute(account_id,from_,to,ctx)→StatementDTO; ReportQuery.execute(Q3…Q7,period,filters,ctx)→ReportDTO; ReconciliationQuery.execute(ctx)→ReconciliationDTO',
        'task': {
            'signature': ['StatementQuery.execute(account_id:int, from_:datetime, to:datetime, ctx:ActorContext) -> StatementDTO', 'ReportQuery.execute(kind:Q3|Q4|Q5|Q6|Q7, period:Period, filters:dict, ctx:ActorContext) -> ReportDTO', 'ReconciliationQuery.execute(ctx:ActorContext) -> ReconciliationDTO'],
            'inputs': {
                'ctx': _CTX, 'account_id': 'int > 0',
                'Period': {'from': 'timezone-aware datetime/RFC 3339', 'to': 'timezone-aware datetime/RFC 3339; from < to; интервал полуоткрытый'},
                'book_boundary': 'book_opened_at из подтверждённого манифеста среза; начало периода не раньше этой границы, иначе BT004/422 с доступной границей.',
                'allowed_filters': {
                    'Q3': {'client_id': 'int > 0, optional', 'account_id': 'int > 0, optional', 'status': 'active|blocked|closed, optional; без фильтра видны все состояния'},
                    'Q4': {'from_account_id': 'int > 0, optional', 'to_account_id': 'int > 0, optional', 'older_than_seconds': 'int >= 0, required; возраст от transferred_at до as_of'},
                    'Q5': {'branch_id': 'int > 0, optional', 'min_turnover': 'Decimal >= 0, optional; HAVING суммы отдельно для входящего/исходящего направления'},
                    'Q6': {'loan_id': 'int > 0, optional', 'account_id': 'int > 0, optional'},
                    'Q7': {'account_id': 'int > 0, optional; участие счёта как отправителя/получателя считается один раз', 'branch_id': 'int > 0, optional; распоряжение отбирается по счёту отправителя'},
                },
                'filter_policy': 'Неизвестный kind, неизвестные ключи фильтра и неверные типы отклоняются; строка не подставляется как SQL. Отсутствующий optional-фильтр не ограничивает набор.',
            },
            'preconditions': ['М10 проверяет актуальный доступ к виду отчёта и объекту; сверка доступна controller.', 'Счёт/явно указанные объекты существуют. Временные границы нормализуются в Europe/Moscow по общей политике; сервер не угадывает часовой пояс.', 'Все части одного ответа читают один согласованный снимок (REPEATABLE READ READ ONLY); as_of указывает его актуальность, а не запрос произвольного прошлого состояния.'],
            'postconditions': {
                'StatementDTO': {'account_id': 'int', 'from': 'datetime', 'to': 'datetime', 'as_of': 'datetime', 'opening_balance': 'Decimal', 'rows': [{'transfer_id': 'int', 'finished_at': 'datetime', 'direction': 'incoming|outgoing', 'amount': 'Decimal > 0', 'balance_after': 'Decimal'}], 'closing_balance': 'Decimal'},
                'statement_rules': ['Только completed текущей книги: from≤finished_at<to. UNION ALL разделяет входящее и исходящее; упорядочение (finished_at,transfer_id).', 'opening_balance результата = сохранённый opening_balance счёта + входящие − исходящие completed текущей книги до from. Для каждой строки balance_after получается из предыдущего остатка; closing_balance совпадает с последним или начальным при пустом наборе.', 'История до book_opened_at не реконструируется из среза; архив не выдаётся за детали текущей книги. Pending/cancelled денег выписки не меняют.'],
                'ReportDTO': 'kind, period, применённые filters, as_of, типизированные rows и totals; деньги передаются по общей политике, пустые суммы/счётчики равны 0.',
                'report_rules': {
                    'Q3': 'Карта–счёт–клиент; expires_on попадает в календарный интервал period в Europe/Moscow; выводятся маска номера, даты, состояние, доступность и целое число дней до expires_on от даты as_of. Blocked/closed видны отдельно.',
                    'Q4': 'Строки pending с transferred_at в period и возрастом >older_than_seconds; cancelled показываются отдельным списком того же периода, не считаются незавершёнными и не включаются в денежный итог.',
                    'Q5': 'Только completed по finished_at в period; отдельные входящие/исходящие агрегаты отделения: COUNT, SUM, AVG. Порог min_turnover применяется к сумме каждого направления; внутренний перевод не превращается в внешний доход.',
                    'Q6': 'Плановые платежи с due_on в календарном period: дата, principal_part, interest_part, сумма; соединение с loan/account. Не выводить факт оплаты или просрочки, которых модель не хранит.',
                    'Q7': 'Когорта transferred_at в period; на общем as_of считать pending/completed/cancelled отдельно. Доля completed = completed/all*100, при all=0 равна 0; as_of обязателен. По finished_at денежную статистику не смешивать с этой когортой.',
                },
                'ReconciliationDTO': 'as_of; accounts[{account_id,stored_balance:Decimal,calculated_balance:Decimal,difference:Decimal}]; inconsistent_loans[{loan_id,reason}]; audit_events с разрешёнными полями И без секретов; totals{account_count,mismatch_count,inconsistent_loan_count}. calculated_balance использует только opening_balance+completed текущей книги; read-only, без автоматической правки расхождений.',
                'representation': _FORMAT,
            },
            'errors': {'AUTH/401': 'нет сеанса', 'BT001/404': 'не найден заданный объект', 'BT002/403': 'запрещён отчёт/объект', 'BT004/422': 'недоступный/обратный период, неверный фильтр или тип; вернуть book_opened_at при нарушении границы', 'BT099/503': 'снимок/БД недоступны; не выдавать частичный документ за полный'},
            'verificationIDs': ['И12', 'И17', 'И19', 'И21', 'И23'],
        },
    },
    'М09': {
        'signature': 'ResultPresenter.render(OutcomeDTO,ctx)→ResultDocument; details — View результата; номер карты — только последние 4; неизвестный исход — отдельное сообщение',
        'task': {
            'signature': ['ResultPresenter.render(outcome:OutcomeDTO, ctx:ActorContext) -> ResultDocument'],
            'inputs': {'ctx': _CTX, 'OutcomeDTO': {'kind': 'client|branch|employee|account|card|transfer|loan|statement|report|reconciliation', 'entity_id': 'int > 0 для предметного объекта; у агрегатного отчёта отсутствует', 'status': 'обязательное сохранённое состояние для account/card/transfer/loan; для client/branch/employee/statement/report/reconciliation отсутствует, новое предметное состояние не изобретается', 'request_id': 'UUID корреляции', 'details': 'ClientView|BranchView|EmployeeView|AccountView|CardView|TransferView|LoanView|StatementDTO|ReportDTO|ReconciliationDTO согласно kind'}},
            'preconditions': ['М10 повторно проверяет активность и право на показ объекта/вида документа.', 'OutcomeDTO получен от доверенного профильного модуля после подтверждённого COMMIT; чтение деталей/связанных итогов использует согласованный снимок М08.', 'kind и details должны согласоваться; ID и состояние не берутся из произвольного клиентского JSON.'],
            'postconditions': {
                'returns': 'ResultDocument{kind,entity_id?,status?,request_id,as_of,details}; status присутствует только для вида с предметным состоянием. Показывает сохранённый результат и понятное основание/сообщение; новый денежный или договорный факт не создаётся.',
                'effects': ['Номер карты во всех отображаемых карточках/списках/подтверждениях маскируется, сохраняются только последние четыре цифры. Секреты и внутренний SQL не выводятся.', 'Неизвестный исход при потере связи — отдельная ветвь сценария М09: сообщение «исход неизвестен», прежний ID/ключ и безопасная сверка GET/повтор. Это не transfer.status и не подтверждение успеха; render подтверждённого OutcomeDTO вызывается после установления исхода.', 'Три маршрута выполняются из связанного клиентского контекста; сохранённые реквизиты вручную не переносятся. Отказ сохраняет введённое для исправления, не имитируя фиксацию.', _FORMAT],
            },
            'errors': {'AUTH/401': 'нет сеанса', 'BT001/404': 'документируемый объект не найден', 'BT002/403': 'показ запрещён/сотрудник отключён', 'BT004/422': 'неизвестный kind или несогласованный тип details', 'BT099/503': 'нет подтверждённого результата; показать отдельное неопределённое состояние сценария', 'INTERNAL/500': 'понятный отказ и request_id без SQL/секретов'},
            'verificationIDs': ['И17', 'И18', 'И19', 'И23', 'И24'],
        },
    },
    'М10': {
        'signature': 'authenticate(login,password)→ActorContext/401; authorize(ctx,action)→allow/BT002; hash_password(password)→внутренний hash для create employee в М01',
        'task': {
            'signature': ['authenticate(login:str,password:str) -> ActorContext / AUTH', 'authorize(ctx:ActorContext,action:Action) -> allow / BT002', 'hash_password(password:str) -> str [внутренний вызов только для создания employee из М01]'],
            'inputs': {'ActorContext': _CTX, 'login': 'str, до 80; общая канонизация', 'password': 'непустой секрет write_only; политика хеширования и её параметры версионируются', 'Action': 'фиксированный код действия и целевого объекта, а не произвольный SQL/путь; неизвестное действие запрещено'},
            'preconditions': ['authenticate сопоставляет login с employee и проверяет пароль библиотечной функцией scrypt по политике 6.4, с индивидуальной солью и фиксированными параметрами; не сравнивает открытый пароль с хешем как строки.', 'authorize принимает только серверный контекст действующего сеанса; на каждом действии повторно читает is_active и актуальную role_code.', 'hash_password вызывается из доверенной ветви создания employee администратором; внешний JSON никогда не задаёт password_hash.'],
            'postconditions': {
                'authenticate': 'При верных данных активного сотрудника возвращает employee_id, актуальную role и UUID request_id; формирует защищённый сеанс. Иначе одинаковый AUTH/401 без раскрытия существования login.',
                'authorize': 'allow только при действующем сеансе, active и разрешённой паре role/action. Переданная клиентом роль/actor_id не принимается. После отключения сотрудник получает отказ и через прежний сеанс.',
                'authorization_scope': {'operator': 'ведение клиентов/счетов/карт и переводов; разрешённые рабочие документы', 'credit': 'регистрация/закрытие утверждённых договоров и чтение необходимого контекста/плана', 'controller': 'разрешённое чтение, отчётность, аудит и независимая сверка без предметных изменений', 'admin': 'справочники, учётные записи, запуск/восстановление; это не автоматическое право проводить переводы/менять договоры'},
                'credential_creation': 'М10 создаёт scrypt-хеш по политике 6.4 с индивидуальной солью и записанными фиксированными параметрами, возвращает его только внутреннему М01. М01 сохраняет employee и аудит одной транзакцией; открытый пароль не сохраняется, не логируется и не попадает в audit_event. Обычный PATCH password/password_hash запрещает.',
                'secrets': 'ActorContext, EmployeeView, ответы ошибок, журналы и аудит не содержат пароль, password_hash или cookie. Проверки не зависят от присланного actor_id.',
            },
            'errors': {'AUTH/401': 'нет сеанса либо неверные/неактивные учётные данные', 'BT002/403': 'нет разрешённого действия или активность отозвана', 'BT004/422': 'неверный формат входа', 'BT099/503': 'невозможно достоверно проверить сеанс/БД; deny by default'},
            'verificationIDs': ['И03', 'И18'],
        },
    },
}

# Для этих пяти модулей точный синтаксис уже напечатан в И/алгоритмах Д.
# JSON связывает его с индивидуальным заданием без повторной печати.
from project_model import MODULES
_EXISTING = {
 'М04': (
  'prepare(cmd,ctx)→TransferView; cancel(id,ctx)→TransferView; resolve_repeat(key,cmd,ctx)→TransferView',
  ['prepare(cmd:TransferCommand,ctx:ActorContext)->TransferView', 'cancel(id:int,ctx:ActorContext)->TransferView', 'resolve_repeat(key:UUID,cmd:TransferCommand,ctx:ActorContext)->TransferView'],
  'TransferCommand и TransferView — contracts/openapi.json; ctx — ActorContext; И Т01–Т02.',
  'Сравнить request_key, параметры и исходного автора. Совпавший повтор возвращает тот же ID и текущее состояние; конфликт — BT005. Создание pending и отмена не меняют деньги; отменяется только pending.',
  ['AUTH','BT001','BT002','BT004','BT005','BT099']),
 'М05': (
  'post(id,ctx)→PostingResult; post_transfer(transfer_id,actor_id,request_id)→jsonb',
  ['post(id:int,ctx:ActorContext)->PostingResult', 'SELECT post_transfer(%s::integer,%s::integer,%s::uuid)'],
  'Положительные transfer_id/actor_id и UUID request_id; actor из сеанса. SQL-граница И Т03–Т08.',
  'Заблокировать перевод и счета в согласованном порядке; повторно проверить состояние, активность и деньги. Остатки, completed, finished_at и аудит фиксируются вместе. Успех возвращается после COMMIT; при потере его подтверждения — сверка того же ID. 40P01/40001: не более трёх попыток с прежним ключом.',
  ['AUTH','BT001','BT002','BT003','BT004','BT005','BT099','INTERNAL']),
 'М06': (
  'validate(cmd)→ValidatedLoan; save(cmd,ctx)→LoanView; close(id,close_ref,ctx)→LoanView',
  ['validate(cmd:LoanCommand)->ValidatedLoan', 'save(cmd:LoanCommand,ctx:ActorContext)->LoanView', 'close(id:int,close_ref:str,ctx:ActorContext)->LoanView'],
  'LoanCommand/LoanView — OpenAPI; ctx — ActorContext; И Т09. Валидированные поля имеют те же типы, что LoanCommand.',
  'Полный договор и график сохраняются атомарно. Уникальный contract_ref сравнивается с утверждёнными условиями: повтор возвращает исходный ID/created_by и текущее состояние, включая closed. Новый договор требует active-счёта; совпавший повтор разрешён и после его отключения. Закрытие требует непустого close_ref, условий и плана не меняет.',
  ['AUTH','BT001','BT002','BT004','BT005','BT006','BT099']),
 'М07': (
  'build(principal,rate,issued_on,due_on,payment_dates)→ScheduleItem[]',
  ['build(principal:Decimal,annual_rate:Decimal,issued_on:date,due_on:date,payment_dates:list[date])->list[ScheduleItem]'],
  'Типы/пределы LoanCommand и ScheduleItem — OpenAPI; алгоритм Д.4 и 6.4.',
  'Principal положителен, ставка 0…999,99 %, даты строго возрастают после issued_on и заканчиваются due_on. Первые N−1 доли floor(principal*100/N) копеек, последняя — остаток; каждая положительна. Проценты по остатку до платежа, фактические дни/365, HALF_UP. Чистый расчёт без записи в БД.',
  ['BT006']),
 'М11': (
  'audit_row(OLD,NEW,actor_id,request_key)→audit_event',
  ['SQL trigger: audit_row(OLD,NEW,transaction_local_actor_id,transaction_local_request_key)'],
  'OLD/NEW предметной строки; доверенные actor_id/request_key из контекста транзакции; И Т05–Т06.',
  'Событие пишется в транзакции предметного изменения и откатывается вместе с ним. Поля audit_event — словарь И; OLD отсутствует для create, NEW содержит результат. Пароли, хеши и cookie исключены; прямые UPDATE/DELETE аудита запрещены. Ошибка записи аудита не подавляется.',
  ['BT099','INTERNAL']),
}
import re
from specifications import ERRORS

def _verification_ids(text):
 result=[]
 for part in text.split(','):
  match=re.fullmatch(r'И(\d+)(?:–И?(\d+))?',part.strip())
  assert match,part
  a=int(match[1]);b=int(match[2] or match[1])
  result.extend(f'И{i:02}' for i in range(a,b+1))
 return result

for _id,_title,_component,_inputs,_result,_rules,_checks in MODULES:
 if _id in _EXISTING:
  _short,_signatures,_input_types,_post,_errors=_EXISTING[_id]
  DETAILS[_id]={'signature':_short,'show_signature':False,'task':{
   'signature':_signatures,'inputs':{'types':_input_types,'domain_input':_inputs},
   'preconditions':[_rules],'postconditions':{'result':_result,'rules':_post},
   'errors':{code:condition+'; HTTP '+http+'; '+handling for code,condition,http,handling in ERRORS if code in _errors},'verificationIDs':_verification_ids(_checks)}}
