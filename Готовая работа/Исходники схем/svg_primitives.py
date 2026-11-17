"""Детерминированные схемы: только геометрия SVG, без генерации изображений ИИ."""
import html, json, re, hashlib
from pathlib import Path
from PIL import ImageFont
from project_model import FIG, SRC, validate_model

FONT_PATH = Path('C:/Windows/Fonts/times.ttf')
class Sheet:
    def __init__(self,name,w=1400,h=700):
        self.name,self.w,self.h=name,w,h
        self.parts=[]; self.boxes=[]; self.texts=[]
    def add(self,s): self.parts.append(s)
    def line(self,pts,arrow=False,dash=False,width=2):
        points=' '.join(f'{x},{y}' for x,y in pts)
        self.add(f'<polyline points="{points}" fill="none" stroke="black" stroke-width="{width}"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="8 5"' if dash else '')+'/>')
    def text(self,x,y,text,size=24,maxw=None,anchor='middle',bold=False,bg=False):
        font=ImageFont.truetype(str(FONT_PATH),size)
        lines=[]
        for para in text.split('\n'):
            words=para.split(' '); line=''
            for word in words:
                candidate=(line+' '+word).strip()
                if maxw and font.getlength(candidate)>maxw and line:
                    lines.append(line);line=word
                else:line=candidate
            lines.append(line)
        widths=[font.getlength(t) for t in lines]
        if maxw: assert max(widths,default=0)<=maxw+2,(self.name,text,max(widths),maxw)
        height=len(lines)*size*1.12
        yy=y-height/2+size*.82
        if bg:
            ww=max(widths)+12
            xx=x-ww/2 if anchor=='middle' else x-6
            self.add(f'<rect x="{xx}" y="{y-height/2-2}" width="{ww}" height="{height+4}" fill="white"/>')
        self.add(f'<text x="{x}" y="{yy:.2f}" text-anchor="{anchor}" font-family="Times New Roman" font-size="{size}" fill="black"'+(' font-weight="bold"' if bold else '')+'>')
        for i,t in enumerate(lines):
            self.add(f'<tspan x="{x}" dy="{0 if i==0 else size*1.12}">{html.escape(t)}</tspan>')
        self.add('</text>')
        self.texts.append({'text':text,'size':size,'lines':len(lines)})
        return height
    def box(self,x,y,w,h,text='',size=24,kind='rect'):
        if kind=='diamond':
            pts=f'{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}'
            self.add(f'<polygon points="{pts}" fill="white" stroke="black" stroke-width="2"/>')
        elif kind=='io':
            pts=f'{x+18},{y} {x+w},{y} {x+w-18},{y+h} {x},{y+h}'
            self.add(f'<polygon points="{pts}" fill="white" stroke="black" stroke-width="2"/>')
        else:
            rx=26 if kind=='terminal' else (10 if kind in ['round','bpmn'] else 0)
            self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="white" stroke="black" stroke-width="2"/>')
        if text:
            ww=w*.68 if kind=='diamond' else w-20
            th=self.text(x+w/2,y+h/2,text,size,ww)
            assert th<=h-8,(self.name,text,th,h)
        self.boxes.append((x,y,w,h))
    def circle(self,x,y,r,label='',thick=False):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" stroke="black" stroke-width="{4 if thick else 2}"/>')
        if label:self.text(x,y,label,24)
    def store(self,x,y,w,h,code,text):
        self.line([(x+w,y),(x,y),(x,y+h),(x+w,y+h)])
        self.line([(x+50,y),(x+50,y+h)])
        self.text(x+25,y+h/2,code,24)
        self.text(x+50+(w-50)/2,y+h/2,text,24,w-65)
    def entity(self,x,y,w,title,rows,size=23):
        head=42; rowh=30; h=head+rowh*len(rows)+8
        self.box(x,y,w,h)
        self.text(x+w/2,y+head/2,title,25,w-16,bold=True)
        self.line([(x,y+head),(x+w,y+head)])
        for i,row in enumerate(rows):
            th=self.text(x+12,y+head+rowh*(i+.5),row,size,w-24,anchor='start')
            assert th<=rowh-3,(self.name,title,row,'Wrapped attribute would overlap next row')
        return h
    def save(self):
        assert all(0<=x and 0<=y and x+w<=self.w+1 and y+h<=self.h+1 for x,y,w,h in self.boxes),self.name
        head=f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}"><defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 9 4 L 0 8" fill="none" stroke="black" stroke-width="1.7"/></marker></defs><rect width="100%" height="100%" fill="white"/>'
        svg=head+'\n'.join(self.parts)+'</svg>'
        p=FIG/(self.name+'.svg');p.write_text(svg,encoding='utf-8')
        return {'name':self.name,'width':self.w,'height':self.h,'min_font_px':min(t['size'] for t in self.texts),'sha256_svg':hashlib.sha256(p.read_bytes()).hexdigest()}











def algorithm():
    s=Sheet('G1_posting',1400,760)
    s.box(50,15,310,55,'Начало',24,'terminal')
    s.box(50,105,310,70,'order_id\nсотрудник',24,'io')
    s.box(50,210,310,100,'Проверить полномочия\nBEGIN; READ COMMITTED',24)
    s.box(50,330,310,75,'Блокировать поручение\nSELECT FOR UPDATE',24)
    s.box(85,440,240,100,'Уже\ncompleted',24,'diamond')
    s.box(85,585,240,100,'Статус\npending',24,'diamond')
    for a,b in [(70,105),(175,210),(310,330),(405,440),(540,585)]:s.line([(205,a),(205,b)],True)
    s.box(430,350,280,85,'Вернуть прежний\ntransfer_id; COMMIT',24)
    s.box(430,465,280,55,'Конец',24,'terminal')
    s.line([(325,490),(380,490),(380,392),(430,392)],True);s.text(360,450,'Да',23,bg=True)
    s.line([(570,435),(570,465)],True)
    s.box(430,600,280,80,'ROLLBACK\nОшибка состояния',24)
    s.line([(325,635),(430,640)],True);s.text(380,610,'Нет',23,bg=True)
    s.box(430,710,280,45,'Конец',24,'terminal');s.line([(570,680),(570,710)],True)
    s.circle(205,725,18,'А');s.line([(205,685),(205,707)],True);s.text(245,700,'Да',23,bg=True)
    s.text(250,565,'Нет',23,bg=True)
    s.circle(975,40,18,'А')
    s.box(805,90,340,80,'Блокировать оба счёта\nпо возрастанию account_id',24)
    s.line([(975,58),(975,90)],True)
    s.box(830,205,290,110,'Все проверки\nвыполнены',24,'diamond')
    s.line([(975,170),(975,205)],True)
    s.box(805,365,340,75,'Списать и зачислить\nодинаковую сумму',24)
    s.line([(975,315),(975,365)],True);s.text(1010,340,'Да',23,bg=True)
    s.box(805,485,340,100,'Создать transfer;\nзавершить поручение;\nзаписать аудит',24)
    s.line([(975,440),(975,485)],True)
    s.box(805,630,340,70,'COMMIT; вернуть transfer_id',24)
    s.line([(975,585),(975,630)],True)
    s.box(1180,340,205,100,'ROLLBACK\nКод ошибки',24)
    s.line([(1120,260),(1280,260),(1280,340)],True);s.text(1240,235,'Нет',23,bg=True)
    s.box(1180,630,205,70,'Конец',24,'terminal')
    s.line([(1280,440),(1280,630)],True);s.line([(1145,665),(1180,665)],True)
    return s.save()


def concurrency():
    s=Sheet('G3_concurrency')
    xs=[260,790,1230]
    s.text(260,35,'Соединение T1',26,bold=True);s.text(790,35,'Счёт A',26,bold=True);s.text(1230,35,'Соединение T2',26,bold=True)
    for x in xs:s.line([(x,80),(x,640)],dash=True)
    s.box(660,90,260,65,'balance = 10 000',24)
    s.line([(260,200),(790,200)],True);s.text(490,170,'Блокировка A',24,bg=True)
    s.line([(1230,260),(790,260)],True);s.text(1020,228,'Попытка блокировки',24,bg=True)
    s.box(1050,315,330,70,'Ожидание COMMIT T1',24)
    s.box(20,315,480,100,'T1 проверяет 10 000 ≥ 7000\nи проводит A→B\nCOMMIT; A = 3000',24)
    s.line([(260,450),(790,450)],True);s.text(510,432,'Освобождение блокировки',23,bg=True)
    s.line([(790,515),(1230,515)],True);s.text(1010,480,'Новый остаток 3000',24,bg=True)
    s.box(1020,560,360,90,'T2: 3000 < 7000\nBT003; ROLLBACK',24)
    s.text(530,675,'Сумма средств сохранена. Ровно одно списание. Возможен симметричный порядок T2 → T1.',24,1310)
    return s.save()
