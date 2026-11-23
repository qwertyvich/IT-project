"""Предметные BPMN: альтернативы команд и устанавливаемый исход записи."""
from diagram_tools import BPMN, Picture, BLUE, GREEN, YELLOW


class Detail(BPMN):
    def __init__(self, name, role):
        Picture.__init__(self, name, 2600, 1500)
        self.nodes = {}; self.seq = []; self.kinds = {}
        self.operations = set(); self.data_count = 0; self.data_inputs = 0; self.data_outputs = 0
        self.add('<rect x="10" y="25" width="2580" height="1365" fill="white" stroke="black" stroke-width="2"/>')
        self.add('<rect x="90" y="235" width="2500" height="1155" fill="#F7F7F7"/>')
        self.line([(90,25),(90,1390)])
        self.line([(10,235),(2590,235)])
        for cy, title in [(130,role),(810,'Банковская система')]:
            self.add(f'<g transform="rotate(-90 50 {cy})">')
            self.text(50,cy,title,24,180 if cy==130 else 800)
            self.add('</g>')
        self.add('<defs><marker id="dataArrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M1,1 L9,5 L1,9" fill="none" stroke="black" stroke-width="1.4"/></marker></defs>')

    def task_at(self, key, x, y, text, w=500, h=130, human=False, ops=()):
        self.filled(x,y,w,h,text,YELLOW if human else BLUE,24,True)
        self.nodes[key]=(x,y,w,h); self.kinds[key]='task'
        self.operations.update(ops)

    def gate_at(self,key,x,cy,label):
        self.box(x,cy-34,68,68,'×',34,'diamond')
        self.text(285 if key=='kind' else x+34,cy-88,label,24,260,bg=True)
        self.nodes[key]=(x,cy-34,68,68); self.kinds[key]='gateway'

    def event_at(self,key,x,cy,label,end=False):
        self.circle(x,cy,22,thick=end)
        self.text(max(195,min(x,self.w-195)),cy+66,label,24,300)
        self.nodes[key]=(x-22,cy-22,44,44)
        self.kinds[key]='end' if end else 'start'

    def data_at(self,x,y,w,title,target,store=False,route=()):
        h=80
        if store:
            self.add(f'<path d="M{x},{y+15} C{x},{y-5} {x+w},{y-5} {x+w},{y+15} V{y+h-15} C{x+w},{y+h+5} {x},{y+h+5} {x},{y+h-15} Z" fill="{GREEN}" stroke="black" stroke-width="2"/>')
            self.add(f'<ellipse cx="{x+w/2}" cy="{y+15}" rx="{w/2}" ry="15" fill="none" stroke="black" stroke-width="2"/>')
        else:
            self.add(f'<path d="M{x},{y} H{x+w-18} L{x+w},{y+18} V{y+h} H{x} Z M{x+w-18},{y} V{y+18} H{x+w}" fill="white" stroke="black" stroke-width="2"/>')
        self.text(x+w/2,y+h/2+7,title,24,w-24)
        tx,ty,tw,th=self.nodes[target]
        pts=[(tx+tw/2,ty+th),*route,(x+w/2,y)]
        if not store: pts.reverse()
        self.add('<polyline points="'+' '.join(f'{a},{b}' for a,b in pts)+'" fill="none" stroke="black" stroke-width="1.6" stroke-dasharray="4 5" marker-end="url(#dataArrow)"/>')
        self.data_count+=1
        if store:self.data_outputs+=1
        else:self.data_inputs+=1

    def begin(self,command):
        self.event_at('start',165,130,'Обращение')
        self.task_at('command',300,75,command,490,110,True)
        self.task_at('check',300,310,'К6 / профильный компонент\nПроверить сеанс, полномочия\nи обязательные реквизиты',490,125)
        self.gate_at('valid',855,372,'Ввод и права\nдопустимы?')
        self.task_at('refusal',1110,310,'Вернуть причину отказа\nбез предметного изменения',490,125)
        self.task_at('result',1900,75,'Прочитать состояние\nи передать результат клиенту',450,110,True)
        self.event_at('end',2490,130,'Результат передан',True)
        self.link('start','command'); self.link('command','check',source='bottom',target='top')
        self.link('check','valid'); self.link('valid','refusal','нет')
        self.link('result','end')
        self.to_result('refusal')

    def to_result(self,node):
        x,y,w,h=self.nodes[node]
        self.link(node,'result',source='right',target='bottom',route=[(2460,y+h/2),(2460,260),(2125,260)])


def cards():
    s=Detail('V3_cards','Оператор')
    s.begin('Выбрать регистрацию,\nпереход состояния или доступность')
    s.gate_at('kind',620,860,'Вид команды?')
    s.link('valid','kind','да',source='bottom',target='left',route=[(889,495),(450,495),(450,860)],labelpos=(930,475))
    branches=[
        ('register',550,'ОП04 · К2\nПроверить уникальный номер,\nсчёт и даты; зарегистрировать','Карта active и авторство\nлибо отказ без записи','Регистрация','ОП04'),
        ('state',825,'ОП05 · К2\nПроверить разрешённый переход;\nиз closed переходов нет','Состояние и аудит\nлибо отказ без изменения','Переход','ОП05'),
        ('availability',1100,'ОП06 · К2\nПроверить active, срок карты\nи открытое состояние счёта','Доступна / недоступна\nна дату запроса;\nбез изменения карты','Доступность','ОП06'),
    ]
    for key,y,task,out,label,op in branches:
        s.task_at(key,1010,y,task,560,140,ops=[op]); s.task_at(key+'_out',1840,y,out,510,140)
        port={'register':'top','state':'right','availability':'bottom'}[key]
        route=[(654,y+70)] if port!='right' else [(820,860),(820,y+70)]
        s.link('kind',key,label,source=port,route=route,labelpos=(850,y+40))
        s.link(key,key+'_out'); s.to_result(key+'_out')
    s.data_at(220,1130,430,'ДО4 · Реквизиты карты','check',route=[(545,470),(180,470),(180,1090),(435,1090)])
    s.data_at(1040,1300,540,'Д2; Д5 · Карта и история','state',True,route=[(1290,1010),(1630,1010),(1630,1270),(1310,1270)])
    return s.finish('К2 реализуется М03. Вид команды выбирает одну ветвь; доступность не равна одному лишь сохранённому состоянию.')


def transfers():
    s=Detail('V4_transfers','Оператор')
    s.begin('Указать реквизиты / прежний ID\nи выбрать действие с переводом')
    s.gate_at('kind',620,840,'Вид команды?')
    s.link('valid','kind','да',source='bottom',target='left',route=[(889,490),(450,490),(450,840)],labelpos=(930,470))
    branches=[
        ('prepare',535,'ОП07 · К3\nПодготовить распоряжение;\nпроверить счета, сумму и ключ','ID и pending\nбез движения денег','Подготовка','ОП07'),
        ('cancel',725,'ОП07 · К3\nОтменить только pending;\ncompleted отменять запрещено','cancelled либо отказ\nбез движения денег','Отмена','ОП07'),
        ('repeat',915,'ОП09 · К3\nСопоставить ключ, автора\nи реквизиты с прежним переводом','Прежний ID и состояние\nлибо BT005;\nповторного списания нет','Повтор / чтение','ОП09'),
    ]
    for key,y,task,out,label,op in branches:
        s.task_at(key,1000,y,task,560,130,ops=[op]); s.task_at(key+'_out',1870,y,out,480,130)
        port='top' if key=='prepare' else 'right'
        route=[(654,y+65)] if port=='top' else [(820,840),(820,y+65)]
        s.link('kind',key,label,source=port,route=route,labelpos=(845,y+30))
        s.link(key,key+'_out'); s.to_result(key+'_out')
    s.task_at('post',1000,1115,'ОП08 · К3, К6\nБлокировки; средства; остатки;\nстатус и аудит; COMMIT',560,140,ops=['ОП08'])
    s.link('kind','post','Проведение',source='bottom',route=[(654,1185)],labelpos=(850,1150))
    s.gate_at('known',1670,1185,'Исход установлен?')
    s.link('post','known')
    s.task_at('known_out',1870,1115,'completed после COMMIT\nлибо недостаток средств /\nиной известный отказ\nбез частичного списания',480,140)
    s.task_at('unknown',1870,1280,'GET прежнего ID; нет связи —\nисход неизвестен;\nновый ключ не создавать',480,100)
    s.link('known','known_out','да')
    s.link('known','unknown','нет',source='bottom',route=[(1704,1330)],labelpos=(1735,1295))
    s.to_result('known_out'); s.to_result('unknown')
    s.data_at(220,1110,430,'ДО5 · Распоряжение','check',route=[(545,470),(180,470),(180,1080),(435,1080)])
    s.data_at(1010,1305,550,'Д1; Д3; Д5 · Остатки, перевод, аудит','post',True)
    return s.finish('Деньги меняет только ОП08. Потеря ответа не означает откат; сверка и повтор используют прежний ключ и ID.')


def loans():
    s=Detail('V5_loans','Кредитный специалист')
    s.begin('Указать номер утверждённого\nдоговора, условия и даты плана')
    s.task_at('validate',300,590,'ОП10 · К4 / М06\nНайти contract_ref;\nпроверить реквизиты команды',490,140,ops=['ОП10'])
    s.link('valid','validate','да',source='bottom',target='top',route=[(889,500),(545,500)],labelpos=(930,475))
    s.gate_at('terms',870,660,'Номер договора новый?')
    s.link('validate','terms')
    s.task_at('existing',220,850,'ОП10 · К4 / М06\nСопоставить счёт и все условия;\nпрежний ID, состояние и план\nлибо BT005 без новой записи',560,140,ops=['ОП10'])
    s.link('terms','existing','нет: прежний',source='bottom',target='top',route=[(904,800),(500,800)],labelpos=(1010,765))
    s.to_result('existing')
    s.task_at('calculate',1110,590,'ОП10 / ОП11 · К4\nМ06: счёт и даты; М07: план;\nпервая дата позже начала',520,140,ops=['ОП10','ОП11'])
    s.link('terms','calculate','да')
    s.gate_at('plan',1730,660,'Суммы и сроки\nполного плана верны?')
    s.link('calculate','plan')
    s.task_at('plan_error',1990,590,'Отклонить план;\nдоговор и строки не записывать',360,140)
    s.link('plan','plan_error','нет'); s.to_result('plan_error')
    s.task_at('save',1110,960,'ОП11 · К4 / М06\nРаспознать contract_ref;\nдоговор, план, аудит атомарно',520,140,ops=['ОП11'])
    s.link('plan','save','да',source='bottom',target='top',route=[(1764,850),(1370,850)],labelpos=(1805,810))
    s.gate_at('saved',1730,1030,'Запись подтверждена?')
    s.link('save','saved')
    s.task_at('saved_out',1990,960,'Новый / прежний ID;\nсостояние и полный план',360,140)
    s.task_at('failure',1990,1210,'Ошибка до фиксации — откат;\nнет ответа — повторить\nпрежний contract_ref',360,150)
    s.link('saved','saved_out','да'); s.to_result('saved_out')
    s.link('saved','failure','нет',source='bottom',route=[(1764,1285)],labelpos=(1810,1250)); s.to_result('failure')
    s.data_at(220,1110,430,'ДО6 / ДО7 · Условия и план','validate',route=[(545,790),(180,790),(180,1080),(435,1080)])
    s.data_at(1110,1240,520,'Д4; Д5 · Договор, строки и аудит','save',True)
    return s.finish('Плановые платежи не подтверждают выдачу и погашение. Закрытие по основанию рассматривается отдельно на В.9.')


BUILDERS={'V3_cards':cards,'V4_transfers':transfers,'V5_loans':loans}
