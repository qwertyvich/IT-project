import html,json,math,re,hashlib,textwrap
from pathlib import Path
from PIL import ImageFont
from fonts import ARIAL
from project_model import FIG,SRC
from diagram_catalog import BY_NAME
from svg_primitives import Sheet
import svg_primitives as legacy
BLUE='#A4C8EA';YELLOW='#FFF2B2';ORANGE='#F7A547';GREEN='#D9EAD3'
def q(s): return json.dumps(s,ensure_ascii=False)

def wrap(s,width=19):
    return '\n'.join('\n'.join(textwrap.wrap(p,width=width,break_long_words=False,break_on_hyphens=False)) for p in s.split('\n'))

class Graph:
    def __init__(self,name,rankdir='LR',font=16):
        self.name=name;self.font=font;self.body=[];self.nodes=set();self.edges=[]
        self.body += [f'graph [rankdir={rankdir}, bgcolor="white", pad=.12, nodesep=.35, ranksep=.65, splines=polyline, outputorder=edgesfirst];',
         f'node [fontname="Arial", fontsize={font}, margin=".12,.08", penwidth=1.3];',
         f'edge [fontname="Arial", fontsize={font-1}, color="#333333", penwidth=1.2, arrowsize=.75];']
    def node(self,id,label,shape='box',fill=BLUE,**opts):
        assert id not in self.nodes,(self.name,id);self.nodes.add(id)
        label=wrap(label)
        font=ImageFont.truetype(str(ARIAL),self.font)
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
        previous=legacy.FONT_PATH;legacy.FONT_PATH=ARIAL
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
        short=text
        super().store(x,y,w,h,code,short)
    def save(self):
        item=super().save();item.update(source='svg',paper=BY_NAME[self.name]['paper'])
        return item

class BPMN(Picture):
    def __init__(self,name,lanes,w=1800,h=830):
        super().__init__(name,w,h);self.lanes=lanes;self.top=25;self.bottom=h-110
        self.lh=(self.bottom-self.top)/len(lanes);self.nodes={};self.seq=[];self.kinds={};self.operations=set();self.data_count=0
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
        self.filled(x,y,w,hh,'' if sub else text,YELLOW if user else BLUE,22,True)
        if sub:
            th=self.text(x+w/2,y+(hh-22)/2,text,22,w-24)
            assert th<=hh-24,(self.name,text,th,hh)
            self.box(x+w/2-9,y+hh-21,18,18);self.text(x+w/2,y+hh-12,'+',18)
        self.nodes[id]=(x,y,w,hh)
        self.kinds[id]='task'
        return id
    def gateway(self,id,x,lane,label=''):
        cy=self.top+lane*self.lh+self.lh/2
        self.box(x,cy-34,68,68,'×',34,'diamond')
        if label:self.text(x+34,cy-70,label,23,190)
        self.nodes[id]=(x,cy-34,68,68)
        self.kinds[id]='gateway'
        return id
    def event(self,id,x,lane,label='',end=False):
        cy=self.top+lane*self.lh+self.lh/2
        self.circle(x,cy,22,thick=end)
        if label:self.text(max(195,min(x,self.w-115)),cy+60,label,23,210)
        self.nodes[id]=(x-22,cy-22,44,44)
        self.kinds[id]='end' if end else 'start'
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
        starts={n for n,k in self.kinds.items() if k=='start'};ends={n for n,k in self.kinds.items() if k=='end'}
        assert starts and ends,self.name
        def reachable(seeds,reverse=False):
            visited=set(seeds);todo=list(seeds)
            while todo:
                n=todo.pop()
                for a,b in self.seq:
                    if reverse:a,b=b,a
                    if a==n and b not in visited:visited.add(b);todo.append(b)
            return visited
        assert reachable(starts)==set(self.nodes),('unreachable',self.name)
        assert reachable(ends,True)==set(self.nodes),('no path to end',self.name)
        for n,k in self.kinds.items():
            if k=='gateway':assert sum(a==n for a,b in self.seq)>=2,(self.name,n)
        item=self.save();item.update(operations=sorted(self.operations),data_objects=self.data_count,sequence_connected=True)
        return item
