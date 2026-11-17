"""Реальные графические модели. SVG строится геометрией, DOT — графовым кодом.

Чен: понятия — прямоугольники, отношения — ромбы, атрибуты — овалы.
DFD: внешние участники, процессы и хранилища связаны именованными потоками.
BPMN: дорожки, задачи, XOR, начальные и конечные события, последовательности.
Все графы являются исходными данными; пропущенные связи таблицами не заменяются.
"""
import html, json, math, re, hashlib, textwrap
from pathlib import Path
from project_model import FIG, SRC, ENTITIES, validate_model
from diagram_catalog import FIGURES, BY_NAME
from svg_primitives import Sheet, algorithm, concurrency
import svg_primitives as legacy
from PIL import ImageFont

BLUE='#A4C8EA'; YELLOW='#FFF2B2'; ORANGE='#F7A547'; GREEN='#D9EAD3'

def q(s): return json.dumps(s,ensure_ascii=False)
def wrap(s,width=19):
    return '\n'.join('\n'.join(textwrap.wrap(p,width=width,break_long_words=False,break_on_hyphens=False)) for p in s.split('\n'))

class Graph:
    def __init__(self,name,rankdir='LR',font=16):
        self.name=name;self.body=[];self.nodes=set();self.edges=[]
        self.body += [f'graph [rankdir={rankdir}, bgcolor="white", pad=.12, nodesep=.35, ranksep=.65, splines=polyline, outputorder=edgesfirst];',
         f'node [fontname="Arial", fontsize={font}, margin=".12,.08", penwidth=1.3];',
         f'edge [fontname="Arial", fontsize={font-1}, color="#333333", penwidth=1.2, arrowsize=.75];']
    def node(self,id,label,shape='box',fill=BLUE,**opts):
        assert id not in self.nodes,(self.name,id);self.nodes.add(id)
        label=wrap(label)
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24 if self.name.startswith('B') and 'chen' in self.name else 18)
        ww=max(font.getlength(t) for t in label.split('\n'))+32
        attrs=dict(label=label,shape=shape,style='filled',fillcolor=fill,width=f'{ww/72:.3f}');attrs.update(opts)
        self.body.append(q(id)+' ['+', '.join(k+'='+q(str(v)) for k,v in attrs.items())+'];')
    def edge(self,a,b,label='',**opts):
        self.edges.append((a.split(':')[0],b.split(':')[0],label))
        self.body.append(a+' -> '+b+' ['+', '.join(k+'='+q(str(v)) for k,v in dict(label=wrap(label,18),**opts).items())+'];')
    def rank(self,*ids):self.body.append('{rank=same; '+'; '.join(ids)+';}')
    def save(self):
        for a,b,_ in self.edges:assert a in self.nodes and b in self.nodes,(self.name,a,b)
        dot='digraph '+self.name+' {\n'+'\n'.join(self.body)+'\n}'
        (FIG/(self.name+'.dot')).write_text(dot,encoding='utf-8')
        return dict(name=self.name,source='dot',nodes=len(self.nodes),edges=len(self.edges),paper=BY_NAME[self.name]['paper'])

class Picture(Sheet):
    def text(self,x,y,text,size=24,maxw=None,anchor='middle',bold=False,bg=False):
        # Arial для схем; размеры проверяет тот же метрический механизм.
        start=len(self.parts)
        previous=legacy.FONT_PATH;legacy.FONT_PATH=Path('C:/Windows/Fonts/arial.ttf')
        try:val=super().text(x,y,text,size,maxw,anchor,bold,bg)
        finally:legacy.FONT_PATH=previous
        for i in range(start,len(self.parts)):self.parts[i]=self.parts[i].replace('Times New Roman','Arial')
        return val
    def filled(self,x,y,w,h,text='',fill=BLUE,size=24,round=False):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{12 if round else 0}" fill="{fill}" stroke="black" stroke-width="2"/>')
        self.boxes.append((x,y,w,h))
        if text:
            height=self.text(x+w/2,y+h/2,text,size,w-24)
            assert height<h-8,(self.name,text,height,h)
    def process(self,x,y,w,h,code,text,size=24):
        self.filled(x,y,w,h,fill=YELLOW,round=True)
        self.add(f'<path d="M{x+12},{y} H{x+w-12} Q{x+w},{y} {x+w},{y+12} V{y+37} H{x} V{y+12} Q{x},{y} {x+12},{y}" fill="{ORANGE}" stroke="black" stroke-width="2"/>')
        self.text(x+w/2,y+19,code,size)
        self.text(x+w/2,y+37+(h-37)/2,text,size,w-20)
    def store(self,x,y,w,h,code,text):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{GREEN}"/>')
        short={'D1':'Справочники\nи счета','D2':'Поручения\nи реестры','D3':'Переводы\nи возвраты','D4':'Журнал\nаудита'}.get(code,text)
        super().store(x,y,w,h,code,short)
    def save(self):
        item=super().save();item.update(source='svg',paper=BY_NAME[self.name]['paper'])
        return item

def context():
    s=Picture('A1_context',1500,760)
    s.filled(20,310,245,110,'E1\nОператор',size=27)
    s.filled(1235,310,245,110,'E2\nКонтролёр',size=27)
    s.filled(600,15,300,95,'E3\nАдминистратор',size=27)
    s.process(490,280,520,255,'0','Учитывать и контролировать\nвнутрибанковские переводы',29)
    s.line([(265,335),(490,335)],True);s.text(378,245,'Реквизиты клиентов,\nсчета, поручения,\nCSV, команды, период',24,225)
    s.line([(490,485),(380,485),(380,395),(265,395)],True);s.text(265,560,'Карточки, статусы,\nвыписки, ошибки',24,330)
    s.line([(1235,335),(1010,335)],True);s.text(1122,245,'Оригинал и причина\nвозврата, параметры\nконтрольных отчётов',24,225)
    s.line([(1010,485),(1120,485),(1120,395),(1235,395)],True);s.text(1230,560,'Результат возврата,\nотчёты, ошибки',24,340)
    s.line([(660,110),(660,280)],True);s.text(444,159,'Справочники,\nучётные записи,\nнастройки доступа',24,265)
    s.line([(840,280),(840,110)],True);s.text(1070,159,'Подтверждения,\nжурнал действий',24,275)
    s.text(750,655,'Граница автоматизации: операционное подразделение одного банка; рублёвые переводы физических лиц.',25,1450)
    s.text(750,715,'DFD (Гейн — Сарсон): синий блок — внешний участник; жёлтый — процесс; стрелка — поток данных.',23,1450)
    return s.save()

FUNCTIONS=[('F1','Вести клиентов\nи счета'),('F2','Регистрировать\nпоручения'),('F3','Проводить\nпереводы'),('F4','Возвращать\nпереводы'),('F5','Выдавать выписки\nи отчёты')]
STORE_NAMES={'D1':'Клиенты, счета,\nсотрудники, получатели','D2':'Поручения\nи реестры','D3':'Факты переводов\nи основания возврата','D4':'События\nаудита'}

def dfd_full_readable():
    s=Picture('A2_dfd',2850,1600)
    def tile(ox,oy,code,title,actors,stores):
        # Повторные экземпляры хранилища обозначают тот же информационный ресурс.
        s.process(ox+325,oy+235,280,150,code,title,26)
        if len(actors)==1:
            e,label,inp,out=actors[0]
            s.filled(ox+325,oy+10,280,80,e+' '+label,BLUE,25)
            s.line([(ox+385,oy+90),(ox+385,oy+235)],True)
            s.text(ox+205,oy+153,inp,23,205,bg=True)
            s.line([(ox+545,oy+235),(ox+545,oy+90)],True)
            s.text(ox+715,oy+153,out,23,215,bg=True)
        else:
            for j,(e,label,inp,out) in enumerate(actors):
                x=ox+20+j*(880/(len(actors)-1))
                x=min(x,ox+715)
                s.filled(x,oy+10,200,80,e+'\n'+label,BLUE,23)
                px=ox+365+j*85
                s.line([(x+70,oy+90),(x+70,oy+145),(px,oy+145),(px,oy+235)],True)
                s.line([(px+32,oy+235),(px+32,oy+185),(x+140,oy+185),(x+140,oy+90)],True)
                s.text(x+100,oy+125,inp,21,205,bg=True)
                s.text(x+100,oy+208,out,21,215,bg=True)
        positions={'D1':(ox+10,oy+280),'D2':(ox+705,oy+280),'D3':(ox+105,oy+570),'D4':(ox+605,oy+570)}
        for d,read,write in stores:
            x,y=positions[d];s.store(x,y,220,95,d,STORE_NAMES[d])
            # Метки находятся в свободных коридорах, не заменяются сносками.
            if d=='D1':
                if read:s.line([(x+220,y+20),(ox+325,oy+300)],True);s.text(ox+157,oy+250,read,22,260,bg=True)
                if write:s.line([(ox+325,oy+350),(x+220,y+72)],True);s.text(ox+165,oy+420,write,22,270,bg=True)
            elif d=='D2':
                if read:s.line([(x,y+20),(ox+605,oy+300)],True);s.text(ox+785,oy+250,read,22,270,bg=True)
                if write:s.line([(ox+605,oy+350),(x,y+72)],True);s.text(ox+790,oy+420,write,22,270,bg=True)
            else:
                portx=ox+(405 if d=='D3' else 525)
                if read:
                    s.line([(x+75,y),(x+75,oy+490),(portx-35,oy+490),(portx-35,oy+385)],True)
                    s.text(x+5,oy+487,read,22,240,bg=True)
                if write:
                    s.line([(portx,oy+385),(portx,oy+530),(x+155,oy+530),(x+155,y)],True)
                    s.text(x+175,oy+480,write,22,240,bg=True)
    tile(0,0,'F1','Вести клиентов\nи счета',[
      ('E1','Оператор','Реквизиты','Карточки'),('E3','Администратор','Настройки','Подтверждения')],[
      ('D1','Текущие данные','Карточки; доступ'),('D4','','Аудит изменений')])
    tile(950,0,'F2','Регистрировать\nпоручения',[
      ('E1','Оператор','Поручение; отмена; CSV','Статусы; ошибки')],[
      ('D1','Счета; права',''),('D2','Ключ; хеш; статус','Поручения; реестр'),('D4','','Аудит поручений')])
    tile(1900,0,'F3','Проводить\nпереводы',[
      ('E1','Оператор','Команда проведения','transfer_id; ошибка')],[
      ('D1','Остатки; состояния','Новые остатки'),('D2','Поручение','completed'),('D3','','Обычный перевод'),('D4','','Аудит проведения')])
    tile(380,790,'F4','Возвращать\nпереводы',[
      ('E2','Контролёр','Оригинал; причина; ключ','Результат возврата')],[
      ('D1','Остатки; состояния','Новые остатки'),('D3','Оригинал; возврат','Обратный факт; основание'),('D4','','Аудит возврата')])
    tile(1590,790,'F5','Выдавать выписки\nи отчёты',[
      ('E1','Оператор','Счёт; период','Выписка'),('E2','Контролёр','Параметры','Отчёты'),('E3','Администратор','Фильтры','Журнал')],[
      ('D1','Клиенты; счета',''),('D2','Поручения',''),('D3','Денежные факты',''),('D4','События','')])
    s.text(1425,1545,'DFD, уровень 1. Повтор E1–E3 или D1–D4 означает тот же объект. Направление стрелки задаёт передачу данных.',24,2750)
    return s.save()

def decomposition():
    s=Picture('A3_functions',1650,830)
    s.process(590,15,470,110,'0','Учитывать и контролировать переводы',27)
    xs=[15,345,675,1005,1335]
    subs=[['F1.1 Регистрировать клиента','F1.2 Открывать и отключать счёт','F1.3 Вести получателей и доступ'],
          ['F2.1 Проверять реквизиты','F2.2 Создавать / отменять','F2.3 Загружать реестр CSV'],
          ['F3.1 Проверять поручение','F3.2 Проводить транзакцию','F3.3 Возвращать итог операции'],
          ['F4.1 Проверять основание','F4.2 Создавать обратный факт','F4.3 Фиксировать результат'],
          ['F5.1 Выдавать выписку Q1','F5.2 Строить отчёты Q2–Q8','F5.3 Показывать журнал']]
    s.line([(825,125),(825,175)]);s.line([(170,175),(1490,175)])
    for (f,title),x,children in zip(FUNCTIONS,xs,subs):
        s.line([(x+155,175),(x+155,220)])
        s.process(x,220,300,132,f,title,25)
        s.line([(x+155,352),(x+155,380),(x+20,380),(x+20,708)])
        for j,t in enumerate(children):
            y=405+j*120;s.line([(x+20,y+35),(x+45,y+35)])
            s.filled(x+45,y,255,92,t,'white',23)
    s.text(825,790,'Декомпозиция показывает состав функций. Последовательность и условия выполнения представлены в BPMN.',24,1580)
    return s.save()

def dfd_detail(name,code,steps,inputs,outputs,reads,writes,links):
    # Каждый лист полностью раскрывает поток своей родительской функции.
    g=Graph(name,'LR',18)
    for id,title in inputs.items():g.node(id,title)
    for id,title in steps.items():g.node(id,id[:2]+'.'+id[2:]+'\n'+title,'box',YELLOW,style='rounded,filled')
    for id,title in outputs.items():g.node(id,title)
    for id,title in {**reads,**writes}.items():g.node(id,id+'\n'+title,'record',GREEN)
    for a,b,t in links:g.edge(a,b,t)
    return g.save()

def details():
    return [
    dfd_detail('A4_directory','F1',{'F11':'Проверить реквизиты\nи полномочия','F12':'Сохранить клиента,\nсчёт или получателя','F13':'Зарегистрировать\nаудит'},
      {'E1':'E1 Оператор','E3':'E3 Администратор'},{}, {'D1':STORE_NAMES['D1']},{'D4':STORE_NAMES['D4']},[
      ('E1','F11','Карточка; реквизиты'),('E3','F11','Справочники; права'),('D1','F11','Дубли; состояние; роль'),('F11','E1','Ошибки реквизитов'),('F11','E3','Отказ доступа'),('F11','F12','Проверенные значения'),('F12','D1','Карточка / изменение'),('F12','F13','Изменение account; автор'),('F13','D4','old/new; ключ; время'),('F12','E1','Карточка и идентификатор'),('F12','E3','Подтверждение настройки')]),
    dfd_detail('A5_orders','F2',{'F21':'Проверить ключ,\nформат и все строки','F22':'Сохранить поручения\nили отменить pending','F23':'Зафиксировать аудит'},
      {'E1':'E1 Оператор'},{},{'D1':STORE_NAMES['D1'],'D2':STORE_NAMES['D2']},{'D4':STORE_NAMES['D4']},[
      ('E1','F21','Реквизиты; отмена; CSV'),('D1','F21','Счета; сотрудник'),('D2','F21','Ключ; хеш; статус'),('F21','E1','Ошибки строк / конфликт'),('F21','F22','Проверенный набор'),('F22','D2','Реестр и поручения; статус'),('F22','F23','Изменения поручений'),('F23','D4','События аудита'),('F22','E1','order_id / batch_id; статус'),('F21','E1','Прежний результат повтора')]),
    dfd_detail('A6_posting','F3',{'F31':'Проверить полномочия\nи состояние поручения','F32':'Проверить средства\nи провести перевод','F33':'Сформировать результат'},
      {'E1':'E1 Оператор'},{},{'D1':STORE_NAMES['D1'],'D2':STORE_NAMES['D2']},{'D3':STORE_NAMES['D3'],'D4':STORE_NAMES['D4']},[
      ('E1','F31','order_id; сеанс'),('D2','F31','Поручение и статус'),('D1','F31','Полномочия сотрудника'),('F31','F32','Допустимое pending'),('D1','F32','Два остатка; состояния'),('F32','D1','Два новых остатка'),('F32','D2','completed; finished_at'),('F32','D3','regular; order_id'),('F32','D4','Аудит остатков и статуса'),('F31','F33','Повтор / ошибка состояния'),('F32','F33','Зафиксированный факт / отказ'),('F33','E1','transfer_id либо код ошибки')]),
    dfd_detail('A7_reversal','F4',{'F41':'Проверить контролёра,\nоригинал и ключ','F42':'Провести полный\nобратный перевод','F43':'Сформировать результат'},
      {'E2':'E2 Контролёр'},{},{'D1':STORE_NAMES['D1'],'D3':STORE_NAMES['D3']},{'D4':STORE_NAMES['D4']},[
      ('E2','F41','original_id; причина; ключ'),('D1','F41','Роль сотрудника'),('D3','F41','Оригинал; существующий возврат'),('F41','F42','Допустимое основание'),('D1','F42','Остатки; состояния'),('F42','D1','Остатки после возврата'),('F42','D3','reversal и transfer_reversal'),('F42','D4','Аудит изменения счетов'),('F41','F43','Повтор / отказ'),('F42','F43','Итог фиксации'),('F43','E2','reversal_transfer_id / ошибка')]),
    dfd_detail('A8_reports','F5',{'F51':'Проверить доступ,\nсчёт и период','F52':'Вычислить выписку\nили агрегаты','F53':'Представить результат\nи время актуальности'},
      {'E1':'E1 Оператор','E2':'E2 Контролёр','E3':'E3 Администратор'},{},{'D1':STORE_NAMES['D1'],'D2':STORE_NAMES['D2'],'D3':STORE_NAMES['D3'],'D4':STORE_NAMES['D4']},{},[
      ('E1','F51','Счёт; период'),('E2','F51','Вид отчёта; период'),('E3','F51','Фильтры журнала'),('D1','F51','Счёт; владелец; роль'),('F51','F52','Допустимый запрос'),('D1','F52','Клиенты; отделения; остатки'),('D2','F52','Поручения и статусы'),('D3','F52','Денежные факты'),('D4','F52','События аудита'),('F52','F53','Строки; итоги; актуальность'),('F51','F53','Ошибка доступа / периода'),('F53','E1','Выписка / ошибка'),('F53','E2','Контрольный отчёт / ошибка'),('F53','E3','Журнал / ошибка')])]

def chen_graph(name,entities,relations):
    g=Graph(name,'TB',24)
    # Фиксированная компоновка Чена: атрибуты окружают каждое понятие,
    # центральные коридоры отданы отношениям. Neato прокладывает линии.
    places={
      'B1_chen_people':{'branch':(450,1200),'employee':(1500,1200),'client':(450,380),'account':(1500,380),'beneficiary':(2500,790)},
      'B2_chen_operations':{'employee':(400,1200),'batch':(1450,1200),'account':(2500,1200),'order':(400,350),'transfer':(1450,350),'reversal':(2500,350)},
      'B3_chen_quality':{'requirement':(400,1200),'case':(1450,1200),'indicator':(2500,1200),'run':(400,350),'observation':(1450,350),'evidence':(2500,350)}
    }[name]
    rplaces={
      'B1_chen_people':[(960,1200),(1040,790),(960,380),(1350,630),(2100,570)],
      'B2_chen_operations':[(920,1200),(400,780),(960,780),(1050,1000),(1700,1000),(2000,850),(950,350),(2350,690),(2000,510),(2000,350),(2200,160)],
      'B3_chen_quality':[(925,1200),(1975,1200),(1450,790),(925,350),(1975,350)]
    }[name]
    def pos(id,xy):g.body.append(f'{id} [pos="{xy[0]/72},{xy[1]/72}!", pin=true];')
    g.body.append('graph [overlap=true, splines=true, notranslate=false];')
    for id,title,attrs in entities:
        g.node(id,title,'box',BLUE)
        cx,cy=places[id];pos(id,(cx,cy))
        offsets=([(0,225),(-300,150),(300,150),(-260,320),(260,320),(0,420)]
                 if cy>700 else [(0,-200),(-300,-120),(300,-120),(-270,-300),(270,-300),(0,-400)])
        for i,att in enumerate(attrs):
            aid=f'{id}_a{i}';key=att.startswith('*');att=att.lstrip('*')
            if key:
                # HTML underline is unambiguous even in monochrome printing.
                g.nodes.add(aid);g.body.append(f'{aid} [shape=ellipse, label=<<U>{html.escape(att)}</U>>, fillcolor="white", style=filled];')
            else:g.node(aid,att,'ellipse','white')
            dx,dy=offsets[i];pos(aid,(cx+dx,cy+dy))
            g.edge(id,aid,'',dir='none',color='#555555',weight='2')
    for i,(a,b,title,ca,cb) in enumerate(relations):
        rid=f'r{i}';g.node(rid,title,'diamond',YELLOW,margin='.03,.02')
        pos(rid,rplaces[i])
        g.edge(a,rid,'',dir='none',headlabel=ca,labeldistance='2.0',labelangle='35',weight='4')
        g.edge(rid,b,'',dir='none',taillabel=cb,labeldistance='2.0',labelangle='35',weight='4')
    item=g.save();item['engine']='neato';return item

def chen_people():
    return chen_graph('B1_chen_people',[
     ('branch','ОТДЕЛЕНИЕ\nbranch',['*Код отделения','Город','Адрес']),
     ('employee','СОТРУДНИК\nemployee',['*Идентификатор сотрудника','Логин','ФИО','Роль','Признак активности']),
     ('client','КЛИЕНТ\nclient',['*Идентификатор клиента','ФИО','Телефон','Электронная почта','Дата регистрации']),
     ('account','СЧЁТ\naccount',['*Номер счёта','Начальный остаток','Текущий остаток','Состояние','Дата открытия']),
     ('beneficiary','СОХРАНЁННЫЙ ПОЛУЧАТЕЛЬ\nbeneficiary',['Псевдоним'])], [
     ('branch','employee','ОБЪЕДИНЯЕТ\nСОТРУДНИКОВ','1','0..N'),('branch','account','ВЕДЁТ','1','0..N'),
     ('client','account','ВЛАДЕЕТ','1','0..N'),('client','beneficiary','СОХРАНЯЕТ','1','0..N'),
     ('account','beneficiary','УКАЗАН\nКАК ПОЛУЧАТЕЛЬ','1','0..N')])

def chen_operations():
    return chen_graph('B2_chen_operations',[
     ('employee','СОТРУДНИК\nконтекст Б.1',['*Идентификатор сотрудника']),
     ('account','СЧЁТ\nконтекст Б.1',['*Номер счёта']),
     ('batch','РЕЕСТР ПОРУЧЕНИЙ\npayment_batch',['*Идентификатор реестра','Имя файла','Хеш файла','Дата создания']),
     ('order','ПОРУЧЕНИЕ\npayment_order',['*Идентификатор поручения','Ключ запроса','Сумма','Состояние','Дата создания','Дата завершения']),
     ('transfer','ПЕРЕВОД\ntransfer',['*Идентификатор перевода','Ключ запроса','Сумма','Вид: regular / reversal','Время проведения']),
     ('reversal','ОСНОВАНИЕ ВОЗВРАТА\ntransfer_reversal',['Причина'])],[
     ('employee','batch','СОЗДАЁТ\nРЕЕСТР','1','0..N'),('employee','order','СОЗДАЁТ\nПОРУЧЕНИЕ','1','0..N'),
     ('employee','transfer','ПРОВОДИТ','1','0..N'),('batch','order','ОБЪЕДИНЯЕТ','0..1','1..N'),
     ('account','order','СЧЁТ\nОТПРАВИТЕЛЯ','1','0..N'),('account','order','СЧЁТ\nПОЛУЧАТЕЛЯ','1','0..N'),
     ('order','transfer','ИСПОЛНЯЕТСЯ\nОБЫЧНЫМ ПЕРЕВОДОМ','0..1','0..1'),
     ('account','transfer','СПИСАНИЕ\nСО СЧЁТА','1','0..N'),('account','transfer','ЗАЧИСЛЕНИЕ\nНА СЧЁТ','1','0..N'),
     ('transfer','reversal','ИСХОДНЫЙ\nОБЫЧНЫЙ ПЕРЕВОД','1','0..1'),
     ('transfer','reversal','ОБРАТНЫЙ\nПЕРЕВОД','1','0..1')])

def quality():
    return chen_graph('B3_chen_quality',[
     ('requirement','ТРЕБОВАНИЕ\nrequirement',['*Код требования','Формулировка','Категория','Версия']),
     ('case','ПРОВЕРКА\ntest_case',['*Код проверки','Название','Действия','Ожидаемый результат']),
     ('indicator','ПОКАЗАТЕЛЬ\nquality_indicator',['*Код показателя','Свойство качества','Метрика','Единица','Порог принятия']),
     ('run','ЗАПУСК\ntest_run',['*Код запуска','Хеш сборки','Хеш данных','Конфигурация среды','Дата и время']),
     ('observation','НАБЛЮДЕНИЕ\nobservation',['*Код наблюдения','Фактический результат','Вердикт']),
     ('evidence','СВИДЕТЕЛЬСТВО\nevidence',['*Код свидетельства','Путь к архиву','SHA-256'])],[
     ('case','requirement','ПРОВЕРЯЕТ\ncoverage','1..N','1..N'),
     ('indicator','case','ОЦЕНИВАЕТСЯ\nПРОВЕРКОЙ','1','1..N'),
     ('case','observation','ДАЁТ РЕЗУЛЬТАТ','1','0..N'),
     ('run','observation','СОДЕРЖИТ','1','1..N'),
     ('evidence','observation','ПОДТВЕРЖДАЕТ','1','1..N')])

# Все FK изображаются линиями. На втором листе только повторные контекстные
# сущности сокращены до ключей; полные атрибуты этих сущностей даны на Б.4.
FK=[('account','client_id','client','client_id'),('account','branch_id','branch','branch_id'),
 ('employee','branch_id','branch','branch_id'),('beneficiary','client_id','client','client_id'),
 ('beneficiary','account_id','account','account_id'),('payment_batch','created_by','employee','employee_id'),
 ('payment_order','batch_id','payment_batch','batch_id'),('payment_order','from_account_id','account','account_id'),
 ('payment_order','to_account_id','account','account_id'),('payment_order','created_by','employee','employee_id'),
 ('transfer','order_id','payment_order','order_id'),('transfer','from_account_id','account','account_id'),
 ('transfer','to_account_id','account','account_id'),('transfer','posted_by','employee','employee_id'),
 ('transfer_reversal','original_transfer_id','transfer','transfer_id'),('transfer_reversal','reversal_transfer_id','transfer','transfer_id'),
 ('audit_event','actor_id','employee','employee_id')]
def logical(name,full,context=()):
    g=Graph(name,'LR',16)
    for id,label,fields in ENTITIES:
        if id not in full and id not in context:continue
        shown=fields if id in full else [f for f in fields if 'PK' in f[2]]
        data=[]
        for field,typ,flags in shown:
            short=flags.replace('FK '+next((b for a,f,b,p in FK if a==id and f==field),'!'),'FK')
            short=short.replace('NULL до завершения','NULL *').replace('NULL для INSERT','NULL *').replace('NULL для DELETE','NULL *').replace('regular / reversal','NN *')
            data.append((field,typ,short))
        # Порт принадлежит всей строке, поэтому связь выходит у нужного
        # атрибута, а не пересекает соседние ячейки на пути к границе таблицы.
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
        cols=[math.ceil(max(font.getlength(row[j]) for row in data)+24) for j in range(3)]
        rows=[]
        for row in data:
            cells=''.join(f'<TD ALIGN="LEFT" WIDTH="{ww}">{html.escape(t)}</TD>' for t,ww in zip(row,cols))
            rows.append(f'<TR><TD PORT="{row[0]}" CELLPADDING="0"><TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6"><TR>{cells}</TR></TABLE></TD></TR>')
        title=html.escape(label)+'<BR/>'+html.escape(id)+('<BR/>контекст Б.4' if id in context else '')
        tab=f'<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6"><TR><TD BGCOLOR="{BLUE}"><B>{title}</B></TD></TR>'+''.join(rows)+'</TABLE>'
        g.nodes.add(id);g.body.append(f'{id} [shape=plain,label=<{tab}>];')
    for a,f,b,p in FK:
        if a in full and b in g.nodes:
            optional=(a=='payment_order' and f=='batch_id') or (a=='transfer' and f=='order_id')
            target='0..1' if optional else '1'
            many='0..1' if (a=='transfer' and f=='order_id') or a=='transfer_reversal' else '0..N'
            if a=='payment_order' and f=='batch_id':many='1..N'
            # Направление: FK → PK. Кратности раскрыты в модели Чена;
            # обязательность и уникальность дополнительно указаны в строках.
            g.edge(f'{a}:{f}',f'{b}:{p}','',arrowhead='normal',arrowsize='.65')
    return g.save()

class BPMN(Picture):
    def __init__(self,name,lanes,w=1800,h=830):
        super().__init__(name,w,h);self.lanes=lanes;self.top=25;self.bottom=h-110
        self.lh=(self.bottom-self.top)/len(lanes);self.nodes={};self.seq=[]
        self.add(f'<rect x="10" y="{self.top}" width="{w-20}" height="{self.bottom-self.top}" fill="white" stroke="black" stroke-width="2"/>')
        for i,t in enumerate(lanes):
            y=self.top+i*self.lh
            if i%2:self.add(f'<rect x="90" y="{y}" width="{w-100}" height="{self.lh}" fill="#F7F7F7"/>')
            self.line([(90,y),(w-10,y)]);self.line([(90,y),(90,y+self.lh)])
            cy=y+self.lh/2
            self.add(f'<text x="50" y="{cy}" text-anchor="middle" transform="rotate(-90 50 {cy})" font-family="Arial" font-size="24">{html.escape(t)}</text>')
    def task(self,id,x,lane,text,w=240,sub=False,user=False):
        hh=126 if sub else 96
        y=self.top+lane*self.lh+self.lh/2-hh/2
        self.filled(x,y,w,hh,'' if sub else text,YELLOW if user else BLUE,24,True)
        if sub:
            th=self.text(x+w/2,y+(hh-22)/2,text,24,w-24)
            assert th<=hh-30,(self.name,text,th,hh)
            self.box(x+w/2-9,y+hh-21,18,18);self.text(x+w/2,y+hh-12,'+',18)
        self.nodes[id]=(x,y,w,hh)
        return id
    def gateway(self,id,x,lane,label=''):
        cy=self.top+lane*self.lh+self.lh/2
        self.box(x,cy-34,68,68,'×',34,'diamond')
        if label:self.text(x+34,cy-70,label,23,190)
        self.nodes[id]=(x,cy-34,68,68)
        return id
    def event(self,id,x,lane,label='',end=False):
        cy=self.top+lane*self.lh+self.lh/2
        self.circle(x,cy,22,thick=end)
        if label:self.text(max(195,min(x,self.w-115)),cy+60,label,23,210)
        self.nodes[id]=(x-22,cy-22,44,44)
        return id
    def link(self,a,b,label='',route=None,source='right',target='left',labelpos=None):
        def port(rect,side):
            x,y,w,h=rect
            return {'right':(x+w,y+h/2),'left':(x,y+h/2),'top':(x+w/2,y),'bottom':(x+w/2,y+h)}[side]
        pa,pb=port(self.nodes[a],source),port(self.nodes[b],target)
        if route is None:
            if pa[1]==pb[1]:pts=[pa,pb]
            else:
                middle=(pa[0]+pb[0])/2;pts=[pa,(middle,pa[1]),(middle,pb[1]),pb]
        else:pts=[pa]+route+[pb]
        self.line(pts,True);self.seq.append((a,b))
        if label:
            xx,yy=labelpos or ((pts[0][0]+pts[1][0])/2,pts[0][1]-23)
            self.text(xx,yy,label,22,240,bg=True)
    def finish(self,note=''):
        self.text(self.w/2,self.h-66,'BPMN 2.0.2: круг — событие; скруглённый блок — задача; ромб × — исключающий шлюз; + — подпроцесс.',22,self.w-70)
        if note:self.text(self.w/2,self.h-28,note,22,self.w-70)
        # Все задачи и события должны быть связаны, из каждого старта достижим конец.
        assert all(id in {a for a,b in self.seq}|{b for a,b in self.seq} for id in self.nodes),self.name
        return self.save()

def bpmn_overview():
    s=BPMN('V1_overview',['Оператор','Система','Контролёр'],2000,880)
    s.event('start',140,0,'Распоряжение')
    s.task('client',225,0,'Проверить клиента\nи реквизиты',240,user=True)
    s.task('order',535,1,'Подготовить поручение\nF2; CSV — В.3',250,sub=True)
    s.task('post',855,1,'Провести\nпоручение (В.4)',250,sub=True)
    s.gateway('ok',1180,1,'Проведено?')
    s.task('statement',1330,0,'Выдать выписку\n(В.6)',245,user=True)
    s.gateway('return',1640,0,'Нужен возврат?')
    s.task('reverse',1500,2,'Оформить возврат\n(В.5)',265,sub=True,user=True)
    s.event('end',1890,0,'Обслужен',True)
    s.task('error',1330,1,'Показать отказ;\nсохранить pending',220)
    s.event('denied',1830,1,'Отказ',True)
    s.link('start','client');s.link('client','order');s.link('order','post');s.link('post','ok')
    s.link('ok','statement','да',route=[(1278,378),(1278,143)],source='right')
    s.link('ok','error','нет',source='bottom',target='bottom',route=[(1214,495),(1440,495)],labelpos=(1260,475))
    s.link('error','denied')
    s.link('statement','return');s.link('return','end','нет')
    s.link('return','reverse','да',source='bottom',target='top',route=[(1674,450),(1632,450)],labelpos=(1715,320))
    s.link('reverse','end',source='right',target='bottom',route=[(1890,612)],labelpos=(1830,645))
    return s.finish('Один пул операционного подразделения банка; дорожки разделяют ответственность участников.')

def bpmn_directory():
    s=BPMN('V2_directory',['Оператор','Прикладной сервис','PostgreSQL'])
    s.event('start',140,0,'Обращение')
    s.task('input',235,0,'Ввести данные клиента\nи реквизиты счёта',255,user=True)
    s.task('validate',570,1,'Проверить сеанс,\nформат и дубли',245)
    s.gateway('valid',890,1,'Допустимы?')
    s.task('save',1050,2,'Создать клиента / счёт;\nаудит; COMMIT',280)
    s.task('show',1410,0,'Получить карточку\nи номер счёта',235,user=True)
    s.event('end',1725,0,'Зарегистрирован',True)
    s.task('error',1070,1,'Показать причины\nотклонения',235)
    s.event('reject',1390,1,'Отклонено',True)
    s.link('start','input');s.link('input','validate');s.link('validate','valid')
    s.link('valid','save','да',source='bottom',target='left',route=[(924,610)],labelpos=(960,530))
    s.link('save','show');s.link('show','end');s.link('valid','error','нет');s.link('error','reject')
    return s.finish('Открытие счёта не создаёт денежного перевода; начальный остаток задаётся до начала работы книги.')

def bpmn_import():
    s=BPMN('V3_import',['Оператор','Прикладной сервис','PostgreSQL'],1900,860)
    s.event('start',140,0,'Реестр CSV');s.task('upload',225,0,'Выбрать файл\nи отправить',235,user=True)
    s.task('parse',535,1,'Проверить UTF8,\nзаголовок, все строки',260)
    s.gateway('valid',875,1,'Есть ошибки?')
    s.task('error',1010,0,'Показать строки\nс ошибками',230)
    s.event('reject',1330,0,'Не загружен',True)
    s.task('lookup',1010,2,'BEGIN; найти реестр\nпо SHA-256',255)
    s.gateway('exists',1345,2,'Уже есть?')
    s.task('save',1475,2,'Создать batch и все\npending; COMMIT',270)
    s.task('result',1490,1,'Вернуть batch_id\nи список поручений',265)
    s.event('end',1820,1,'Загружен',True)
    s.link('start','upload');s.link('upload','parse');s.link('parse','valid')
    s.link('valid','error','да',source='top',target='left',route=[(909,145)],labelpos=(955,230));s.link('error','reject')
    s.link('valid','lookup','нет',source='bottom',target='left',route=[(909,629)],labelpos=(950,530));s.link('lookup','exists')
    s.link('exists','save','нет');s.link('save','result',source='top',target='bottom',route=[(1610,515),(1622,515)])
    s.link('exists','result','да',source='top',target='left',route=[(1379,391)],labelpos=(1410,480));s.link('result','end')
    return s.finish('При ошибке записи весь импорт откатывается. Повтор идентичных байтов возвращает прежний реестр.')



def bpmn_money(name,actor,command,procedure,operation,result,note):
    s=BPMN(name,[actor,'Прикладной сервис C2','PostgreSQL C3'],2150,950)
    s.event('start',150,0,'Команда')
    s.task('command',250,0,command,270,user=True)
    s.task('auth',580,1,'Проверить сеанс\nи полномочия',250)
    s.gateway('access',880,1,'Доступ разрешён?')
    s.event('forbidden',1040,0,'Нет прав',True)
    s.task('begin',1040,1,'BEGIN; вызвать\n'+procedure,300)
    s.task('operation',1040,2,operation,300,sub=True)
    s.gateway('ok',1420,2,'Успех?')
    s.task('rollback',1420,1,'ROLLBACK;\nкод отказа',245)
    s.event('denied',1510,0,'Отклонено',True)
    s.task('commit',1745,1,'COMMIT; вернуть\nрезультат операции',275)
    s.task('show',1745,0,result,275,user=True)
    s.event('end',2090,0,'Завершено',True)
    s.link('start','command');s.link('command','auth');s.link('auth','access')
    s.link('access','forbidden','нет',source='top',target='left',route=[(914,165)],labelpos=(948,295))
    s.link('access','begin','да');s.link('begin','operation',source='bottom',target='top',route=[(1190,585)])
    s.link('operation','ok')
    s.link('ok','commit','да',source='right',target='bottom',route=[(1882,725)],labelpos=(1570,700))
    s.link('commit','show',source='top',target='bottom',route=[(1882,300)])
    s.link('show','end')
    s.link('ok','rollback','нет',source='top',target='bottom',route=[(1454,585),(1542,585)],labelpos=(1500,610))
    s.link('rollback','denied',source='top',target='bottom',route=[(1542,300),(1510,300)])
    return s.finish(note)

def bpmn_posting():
    return bpmn_money('V4_posting','Оператор','Подтвердить\nпоручение','post_transfer',
      'Поручение и счета:\nблокировки; проверки;\nперевод и аудит',
      'Получить transfer_id\nи новые остатки',
      'Отказ сохраняет pending; повтор completed возвращает прежний факт. Граница транзакции принадлежит C2.')

def bpmn_reversal():
    return bpmn_money('V5_reversal','Контролёр','Выбрать оригинал;\nуказать причину и ключ','reverse_transfer',
      'Проверить оригинал;\nфакт и остатки;\nоснование и аудит',
      'Получить идентификатор\nобратного перевода',
      'Повтор ключа возвращает прежний результат. Исходный факт и completed поручения сохраняются.')

def bpmn_reports():
    s=BPMN('V6_reports',['Оператор / контролёр','Прикладной сервис','PostgreSQL'],1850,830)
    s.event('start',140,0,'Запрос');s.task('input',225,0,'Выбрать счёт / отчёт\nи интервал [начало, конец)',300,user=True)
    s.task('validate',600,1,'Проверить доступ;\nпреобразовать время в UTC',280)
    s.gateway('valid',950,1,'Допустим?')
    s.task('query',1110,2,'Выполнить Q1–Q8;\nдля MV обновить сводку',280)
    s.task('present',1460,0,'Показать строки,\nитоги и актуальность',250,user=True)
    s.event('end',1780,0,'Результат',True)
    s.task('error',1120,1,'Показать ошибку\nдоступа / параметров',270);s.event('reject',1480,1,'Отклонён',True)
    s.link('start','input');s.link('input','validate');s.link('validate','valid')
    s.link('valid','query','да',source='bottom',target='left',route=[(984,596)],labelpos=(1025,510));s.link('query','present');s.link('present','end')
    s.link('valid','error','нет');s.link('error','reject')
    return s.finish('Чтение отчётов не изменяет денежные факты. Пустая выборка возвращает нулевые итоги.')

def states():
    s=Picture('V7_states',1500,700)
    s.circle(60,230,12);s.filled(180,160,320,140,'pending\nОжидает проведения',YELLOW,28,True)
    s.filled(1030,70,340,135,'completed\nПроведено',GREEN,28,True)
    s.filled(1030,400,340,135,'cancelled\nОтменено',BLUE,28,True)
    s.line([(72,230),(180,230)],True);s.text(125,175,'Создание',23,bg=True)
    s.line([(500,200),(730,200),(730,138),(1030,138)],True);s.text(765,85,'post_transfer / COMMIT',25,500,bg=True)
    s.line([(500,270),(730,270),(730,468),(1030,468)],True);s.text(770,510,'cancel / COMMIT',25,450,bg=True)
    s.line([(340,160),(340,65),(650,65),(650,230),(500,230)],True);s.text(575,30,'Отказ / ROLLBACK',24,400,bg=True)
    s.box(900,265,540,75,'Полный возврат создаёт новый transfer;\nсостояние поручения остаётся completed',24)
    s.line([(1200,205),(1200,265)],dash=True)
    s.text(750,610,'После завершения реквизиты неизменяемы. Повтор проведения completed возвращает прежний transfer_id.',24,1430)
    s.text(750,665,'Диаграмма состояний: стрелки — разрешённые переходы; подпись задаёт событие и условие фиксации.',23,1430)
    return s.save()

def reversal_algorithm():
    # Исправленный алгоритм явно показывает ветку идемпотентного результата.
    s=Picture('G2_reversal',1550,810)
    s.box(25,20,340,55,'Начало',24,'terminal');s.box(25,110,340,80,'original_id, request_key,\nпричина; проверенный actor',24,'io')
    s.box(25,225,340,80,'Проверить controller; BEGIN;\nблокировать оригинал',24)
    s.box(65,345,260,110,'Есть результат\nэтого ключа?',24,'diamond')
    s.box(25,515,340,95,'Проверить совпадение\nпараметров и автора',24)
    s.box(25,660,340,95,'Прежний id; COMMIT\nлибо BT005; ROLLBACK',24,'io')
    for a,b in [(75,110),(190,225),(305,345)]:s.line([(195,a),(195,b)],True)
    s.line([(195,455),(195,515)],True);s.text(235,485,'Да',23,bg=True);s.line([(195,610),(195,660)],True)
    s.box(495,205,385,105,'Проверить regular и отсутствие\nвозврата; блокировать счета\nпо возрастанию account_id',24)
    s.line([(325,400),(430,400),(430,258),(495,258)],True);s.text(395,363,'Нет',23,bg=True)
    s.box(540,365,295,115,'Активные счета;\nдостаточно средств?',24,'diamond');s.line([(687,310),(687,365)],True)
    s.box(1090,200,405,100,'Создать обратный transfer;\nизменить оба остатка',24)
    s.box(1090,350,405,105,'Создать transfer_reversal;\nзаписать аудит; COMMIT',24)
    s.box(1090,515,405,80,'Вернуть reversal_transfer_id',24,'io')
    s.line([(835,423),(980,423),(980,250),(1090,250)],True);s.text(940,386,'Да',23,bg=True)
    s.line([(1292,300),(1292,350)],True);s.line([(1292,455),(1292,515)],True)
    s.box(495,560,385,90,'ROLLBACK; BT003 / BT006\nлибо ошибка состояния',24)
    s.line([(687,480),(687,560)],True);s.text(730,523,'Нет',23,bg=True)
    s.box(1090,690,405,60,'Конец',24,'terminal');s.line([(1292,595),(1292,690)],True)
    s.line([(880,605),(990,605),(990,720),(1090,720)],True)
    s.line([(365,707),(420,707),(420,780),(1292,780),(1292,750)],True)
    return s.save()

def environment():
    s=Picture('D1_environment',1500,760)
    s.filled(20,105,275,120,'Оператор\nКарточки; поручения',BLUE,26)
    s.filled(20,435,275,120,'Контролёр\nОтчёты; возвраты',BLUE,26)
    s.filled(1195,105,285,120,'Администратор\nДоступ; эксплуатация',BLUE,25)
    s.process(500,240,500,230,'БанкПеревод','Учёт и контроль\nвнутрибанковских переводов',29)
    s.line([(295,140),(500,310)],True);s.text(425,165,'Реквизиты; команды',23,300,bg=True)
    s.line([(500,390),(295,205)],True);s.text(265,295,'Карточки; выписка; итог',23,410,bg=True)
    s.line([(295,470),(500,420)],True);s.text(330,410,'Основание возврата',23,340,bg=True)
    s.line([(500,450),(295,535)],True);s.text(440,574,'Отчёт; номер возврата',23,400,bg=True)
    s.line([(1195,140),(1000,310)],True);s.text(1095,160,'Учётные записи; настройки',23,350,bg=True)
    s.line([(1000,395),(1195,205)],True);s.text(1260,300,'Журнал; состояние',23,340,bg=True)
    s.filled(580,590,340,80,'Среда испытаний\nПМИ и свидетельства',GREEN,25)
    s.line([(750,590),(750,470)],True);s.text(1060,535,'Контрольные действия',23,340,bg=True)
    s.text(750,720,'Рабочие места находятся в защищённой сети банка; расчётные счета и сотрудники принадлежат одному банку.',23,1450)
    return s.save()

def components():
    s=Picture('D2_components',1650,870)
    s.filled(15,300,255,130,'C1 Интерфейс\nКарточки и формы\nВыписки и отчёты',BLUE,25)
    s.filled(410,50,740,710,fill='#F8F8F8',round=True)
    s.text(780,90,'C2 Прикладной сервис — модульный монолит',27,bold=True)
    blocks=[(450,140,'M1 Справочники','Клиент; счёт; получатель'),(800,140,'M2 Поручения','Создание; отмена; CSV'),
      (450,320,'M3 Проведение','Транзакция; повтор'),(800,320,'M4 Возврат','Основание; обратный факт'),
      (450,500,'M5 Аналитика','Q1–Q8; время отчёта'),(800,500,'Общие механизмы','Сеанс; роли; ошибки')]
    for x,y,title,body in blocks:s.process(x,y,310,130,title,body,23)
    s.text(780,705,'BEGIN → функция БД → COMMIT / ROLLBACK',25,680)
    s.filled(1310,180,320,340,fill=GREEN,round=True)
    s.text(1470,225,'C3 PostgreSQL',27,bold=True)
    s.text(1470,355,'core: предметные данные\nДенежные функции\nОграничения и триггеры\nЖурнал audit_event\nVIEW и MV',24,290)
    s.line([(270,330),(410,330)],True);s.text(340,265,'HTTPS\nJSON / CSV',23,130,bg=True)
    s.line([(410,440),(270,440)],True);s.text(340,500,'Результат\nили ошибка',23,130,bg=True)
    s.line([(1150,330),(1310,330)],True);s.text(1230,260,'SQL\nEXECUTE',23,140,bg=True)
    s.line([(1310,440),(1150,440)],True);s.text(1230,510,'Строки\nSQLSTATE',23,145,bg=True)
    s.filled(1250,625,380,110,'C4 Миграции и испытания\nDDL; данные; quality; архив',YELLOW,24)
    s.line([(1440,625),(1440,520)],True);s.text(1535,575,'Схема; ПМИ',22,185,bg=True)
    s.text(825,825,'C1 не изменяет остатки напрямую. C3 фиксирует денежные факты и аудит атомарно; C4 обслуживает жизненный цикл.',23,1600)
    return s.save()

def deployment():
    s=Picture('D3_deployment',1650,820)
    s.box(15,20,1620,735);s.text(825,53,'Защищённая сеть банка',27,bold=True)
    s.filled(50,130,290,170,'Рабочие места\nБраузер\nОператор / контролёр\nПять сеансов',BLUE,25)
    s.box(460,100,1120,450);s.text(1020,130,'Сервер приложения и БД; Docker Compose',26)
    s.filled(520,225,300,175,'app: C1 + C2\nPython 3.12\nFastAPI + psycopg\nHTTPS через прокси',YELLOW,25)
    s.filled(1120,225,350,175,'db: C3\nPostgreSQL 18\nTCP 5432 внутри сети\nproject_net',GREEN,25)
    s.filled(1120,450,350,65,'Именованный том pgdata',GREEN,24)
    s.line([(340,215),(520,282)],True);s.text(418,172,'HTTPS',23,bg=True)
    s.line([(820,310),(1120,310)],True);s.text(970,270,'SQL; внутренняя сеть',23,285,bg=True)
    s.line([(1295,400),(1295,450)],True)
    s.filled(50,570,550,125,'Отдельная среда испытаний: C4\n4 логических ядра; 8 Гбайт ОЗУ; SSD\nСинтетические данные; quality; журналы',BLUE,24)
    s.filled(1090,590,420,105,'Хранилище резервных копий\npg_dump; контрольные суммы',GREEN,25)
    s.line([(1295,515),(1295,590)],True);s.text(1480,557,'Копия',22,bg=True)
    s.line([(600,632),(900,632),(900,400),(1120,400)],True,dash=True);s.text(805,595,'Проверка; восстановление\nв отдельную БД',23,385,bg=True)
    s.text(825,790,'Секреты вне репозитория; healthcheck; миграции до запуска. Порт БД доступен только сервису и средствам администрирования.',22,1600)
    return s.save()

def main():
    validate_model()
    catalog=[context(),dfd_full_readable(),decomposition()]+details()+[
     chen_people(),chen_operations(),quality(),
     logical('B4_logical_people',{'branch','client','account','employee','beneficiary'}),
     logical('B5_logical_operations',{'payment_batch','payment_order','transfer','transfer_reversal','audit_event'},{'account','employee'}),
     bpmn_overview(),bpmn_directory(),bpmn_import(),bpmn_posting(),bpmn_reversal(),bpmn_reports(),states(),
     algorithm(),reversal_algorithm(),concurrency(),environment(),components(),deployment()]
    for i in catalog:
        i.update(paper=BY_NAME[i['name']]['paper'],caption=BY_NAME[i['name']]['caption'])
        if 'source' not in i:i['source']='svg'
    assert len(catalog)==len(FIGURES)==26
    (SRC/'figures_manifest.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    (SRC/'foreign_keys.json').write_text(json.dumps(FK,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Created {len(catalog)} diagram sources; {len(FK)} foreign keys represented')

if __name__=="__main__":main()
