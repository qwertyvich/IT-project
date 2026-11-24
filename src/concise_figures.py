"""Две компактные декларативные модели для печатной записки.

Старые 36 рисунков не изменяются. Стрелки ER обозначают FK → PK;
на модели качества связи именованы и не задают порядок выполнения.
"""
from pathlib import Path
import hashlib,json,re
from fonts import ARIAL
from PIL import ImageFont
from project_model import FIG,ENTITIES,FK
from diagram_tools import Picture,BLUE,GREEN,YELLOW
from chen_figure import chen_model


class CompactPicture(Picture):
    def __init__(self,name,width,height,out_dir):
        super().__init__(name,width,height)
        self.out_dir=Path(out_dir);self.out_dir.mkdir(parents=True,exist_ok=True)

    def save(self):
        assert all(0<=x and 0<=y and x+w<=self.w+1 and y+h<=self.h+1 for x,y,w,h in self.boxes)
        head=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
              f'viewBox="0 0 {self.w} {self.h}"><defs><marker id="arrow" markerWidth="12" '
              'markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse">'
              '<path d="M 0 0 L 11 5 L 0 10" fill="none" stroke="black" stroke-width="2.4"/>'
              '</marker></defs><rect width="100%" height="100%" fill="white"/>')
        svg=head+'\n'.join(self.parts)+'</svg>'
        path=self.out_dir/(self.name+'.svg');path.write_text(svg,encoding='utf-8')
        minimum=min(t['size'] for t in self.texts)
        scale=min(252/self.w,145/self.h)*72/25.4
        assert minimum*scale>=8.5,(self.name,minimum*scale)
        return {'name':self.name,'source':'svg','path':str(path),'width':self.w,'height':self.h,
                'paper':'A4','orientation':'landscape','max_width_mm':252,'max_height_mm':145,
                'min_font_px':minimum,'min_font_on_paper_pt':round(minimum*scale,2),
                'sha256_svg':hashlib.sha256(path.read_bytes()).hexdigest()}


def data_model(out_dir=FIG/'concise'):
    s=CompactPicture('C_A1_data',2800,1950,out_dir)
    # Поля сгруппированы по строкам только для вёрстки; каждое присутствует явно.
    groups={
      'branch':[('branch_id','branch_code'),('city','address')],
      'employee':[('employee_id','branch_id'),('login',),('password_hash','full_name'),('role_code','is_active')],
      'audit_event':[('event_id','actor_id'),('entity_type','entity_id'),('action','occurred_at'),('request_key',),('old_data','new_data')],
      'client':[('client_id',),('full_name',),('phone','email'),('registered_at',)],
      'account':[('account_id','account_number'),('client_id','branch_id'),('opened_on','status'),('opening_balance','balance')],
      'bank_card':[('card_id','card_number'),('account_id','issued_by'),('issued_on','expires_on'),('status',)],
      'loan_schedule':[('loan_id','payment_no'),('due_on',),('principal_part','interest_part')],
      'loan':[('loan_id',),('contract_ref',),('account_id','created_by'),('principal','annual_rate'),('issued_on','due_on'),('status','close_ref')],
      'transfer':[('transfer_id',),('from_account_id',),('to_account_id','created_by'),('amount','status'),('transferred_at','finished_at'),('request_key',)],
    }
    positions={
      'branch':(60,50),'employee':(1000,50),'audit_event':(1940,50),
      'client':(60,600),'account':(1000,600),'bank_card':(1940,600),
      'loan_schedule':(60,1150),'loan':(1000,1150),'transfer':(1940,1150),
    }
    width,head,rowh=800,92,52
    boxes={}
    specs={name:(title,fields) for name,title,fields in ENTITIES}
    for name,(x,y) in positions.items():
        title,fields=specs[name]
        assert {f for row in groups[name] for f in row}=={f for f,_,_ in fields},name
        height=head+rowh*len(groups[name])+14
        boxes[name]=(x,y,width,height)
    # 12 именованных ссылок. Все линии строятся до объектов, чтобы не заходить в их текст.
    routes={
      ('account','client_id'):[(1000,760),(930,760),(930,716),(860,716)],
      ('account','branch_id'):[(1400,600),(1400,500),(460,500),(460,260)],
      ('employee','branch_id'):[(1000,180),(860,180)],
      ('bank_card','account_id'):[(1940,740),(1800,740)],
      ('bank_card','issued_by'):[(2340,600),(2340,475),(1650,475),(1650,364)],
      ('transfer','from_account_id'):[(2180,1150),(2180,1030),(1280,1030),(1280,914)],
      ('transfer','to_account_id'):[(2480,1150),(2480,1100),(1520,1100),(1520,914)],
      ('transfer','created_by'):[(2740,1280),(2770,1280),(2770,20),(1400,20),(1400,50)],
      ('loan','account_id'):[(1400,1150),(1400,914)],
      ('loan','created_by'):[(1200,1568),(1200,1605),(20,1605),(20,410),(1200,410),(1200,364)],
      ('loan_schedule','loan_id'):[(860,1260),(1000,1260)],
      ('audit_event','actor_id'):[(1940,180),(1800,180)],
    }
    labelpos={
      1:(930,825),2:(1445,550),3:(930,130),4:(1870,690),5:(2110,448),
      6:(1790,990),7:(1790,1060),8:(2690,1050),9:(1450,960),10:(600,1560),
      11:(930,1210),12:(1870,130),
    }
    assert set(routes)=={(child,field) for child,field,_,_ in FK}
    for number,(child,field,parent,target) in enumerate(FK,1):
        s.line(routes[child,field],True,width=3)
        s.text(*labelpos[number],f'R{number}',42,125,bg=True)
    for name,(x,y,w,h) in boxes.items():
        title,fields=specs[name];flags={f:fl for f,_,fl in fields}
        s.filled(x,y,w,h,fill='white')
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{head}" fill="{BLUE}" stroke="black" stroke-width="2"/>')
        s.text(x+w/2,y+30,title,44,w-24,bold=True)
        s.text(x+w/2,y+68,name,42,w-24)
        for row,fieldnames in enumerate(groups[name]):
            values=[]
            for field in fieldnames:
                keys=[key for key in ['PK','FK','UQ'] if key in flags[field]]
                values.append(('/'.join(keys)+' ' if keys else '')+field)
            line='; '.join(values)
            htext=s.text(x+18,y+head+rowh*(row+.5),line,42,w-36,anchor='start')
            assert htext<=rowh-3,(name,line,htext)
    labels=[
      'R1 счёт → клиент','R2 счёт → отделение','R3 сотрудник → отделение',
      'R4 карта → счёт','R5 карта → регистратор','R6 перевод → счёт списания',
      'R7 перевод → счёт зачисления','R8 перевод → создатель','R9 договор → счёт',
      'R10 договор → создатель','R11 платёж → договор','R12 аудит → автор',
    ]
    for index,text in enumerate(labels):
        s.text(70+(index%3)*920,1640+(index//3)*52,text,42,875,anchor='start')
    s.text(1400,1870,'PK — ключ; FK — ссылка; UQ — уникальность. FK → PK: у дочерней записи 1 родитель, у родителя 0..N записей.',42,2680)
    s.text(1400,1920,'entity_id аудита — идентификатор объекта без общего FK. Пересечение линий без узла не создаёт отношения.',42,2680)
    item=s.save();item.update(entities=9,attributes=64,foreign_keys=12,
       entity_attributes={name:[field for field,_,_ in fields] for name,_,fields in ENTITIES},
       relationships=[{'id':f'R{i}','from':a,'field':f,'to':b,'target':k} for i,(a,f,b,k) in enumerate(FK,1)],
       notation='ER: отношения, атрибуты и именованные FK→PK; не нотация Чена')
    return item


def quality_model(out_dir=FIG/'concise'):
    s=CompactPicture('C_A2_quality',2800,1450,out_dir)
    width,height=500,370
    nodes=[
      ('Назначение','Организатор\nРезультат деятельности\nГраницы применения',70,70,BLUE),
      ('Критерий','Фактор и свойство\nПроверяемая грань\nЦП1–ЦП4; свойства результата',790,70,YELLOW),
      ('Метрика','Q; L; u=L/Q\nВремя обращения\nЧисло нарушений',1510,70,YELLOW),
      ('Норма','Порог и условия\nКритические запреты\nВерсия согласования',2230,70,GREEN),
      ('Решение','Соответствует\nНе соответствует\nНедостаточно\nсвидетельств',70,790,BLUE),
      ('Свидетельство','Документ; SQL-срез\nЖурнал; файл\nКонтрольная сумма',790,790,GREEN),
      ('Наблюдение','run_id; факт\nИсполнитель; условия\nМомент измерения',1510,790,GREEN),
      ('Методика','Сценарий испытания\nВход; действия\nЭталон; способ измерения',2230,790,YELLOW),
    ]
    for title,attrs,x,y,color in nodes:
        s.filled(x,y,width,height,fill='white')
        s.add(f'<rect x="{x}" y="{y}" width="{width}" height="90" fill="{color}" stroke="black" stroke-width="2"/>')
        s.text(x+width/2,y+45,title,44,width-25,bold=True)
        s.text(x+width/2,y+225,attrs,42,width-30)
    edges=[
      ([(570,255),(790,255)],(680,200),'задаёт',200),
      ([(1290,255),(1510,255)],(1400,200),'имеет',200),
      ([(2010,255),(2230,255)],(2120,200),'сравнение',215),
      ([(2480,440),(2480,790)],(2480,610),'задаёт эталон',500),
      ([(2230,975),(2010,975)],(2120,920),'порождает',210),
      ([(1510,975),(1290,975)],(1400,920),'имеет',200),
      ([(790,975),(570,975)],(680,920),'основание',210),
      ([(2730,255),(2770,255),(2770,1290),(320,1290),(320,1160)],(1410,1240),'Решение сопоставляет факты и свидетельства с каждой нормой',2300),
    ]
    for points,position,text,maxw in edges:
        s.line(points,True,width=3);s.text(*position,text,40,maxw,bg=True)
    s.text(1400,1380,'Именованные связи не задают очередность действий. До испытаний факты и вердикты не заполнены.',40,2680)
    item=s.save();item.update(quality_objects=8,relationships=8,
      notation='Концептуальная схема объектов и отношений системы оценивания')
    return item


def build_all(out_dir=FIG/'concise'):
    return [chen_model(out_dir),data_model(out_dir),quality_model(out_dir)]


if __name__=='__main__':print(json.dumps(build_all(),ensure_ascii=False,indent=2))
