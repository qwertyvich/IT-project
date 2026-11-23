"""Процессы с явными операциями и ассоциациями информационных объектов."""
from diagram_tools import BPMN,Picture,BLUE,GREEN,YELLOW

SPECS=[
 ('V1_service','Сотрудник банка','Уточнить обращение\nи проверить основания','Получить единый\nклиентский контекст','Выполнить профильный\nподпроцесс по В.2–В.6,\nВ.8–В.9','Проверить и передать\nдокумент клиенту',[],[],['ДО1 / ДО3\nОснования обращения','Д1–Д5\nУчёт и история'],'Результат обращения оценивается в целом; труд сверки и исправлений включается в И24.'),
 ('V2_clients','Оператор','Проверить документы\nи выбрать команду','Проверить полномочия,\nклиента и номер счёта','Сохранить клиента /\nоткрыть счёт по команде','Получить карточку\nи реквизиты счёта',[],['ОП01','ОП02'],['ДО1 / ДО3\nКлиент и счёт','Д1; Д5\nКонтекст и аудит'],'ОП01 и ОП02 — разные команды. Если счёт не открыт, ранее сохранённая карточка клиента остаётся.'),
]
# The rest of each specification is explicit rather than inferred from a caption.
SPECS += [
 ('V3_cards','Оператор','Выбрать регистрацию\nили команду состояния','Проверить счёт, номер,\nдаты и переход','Выполнить выбранное:\nрегистрацию / переход /\nоценку доступности','Получить состояние\nи доступность карты',[],['ОП04','ОП05','ОП06'],['ДО4\nРеестр карт','Д2; Д5\nКарта и история'],'Вид команды выбирает одну операцию ОП04/ОП05/ОП06. Срок и состояние счёта участвуют в оценке доступности.'),
 ('V4_transfers','Оператор','Указать перевод\nи подтвердить действие','Проверить роль,\nреквизиты и вид команды','Выполнить выбранное:\nподготовку / отмену /\nпроведение / повтор','Получить ID, состояние\nи выписку',[],['ОП07','ОП08','ОП09'],['ДО5\nРаспоряжение','Д1; Д3; Д5\nДеньги и аудит'],'Вид команды определяет ветвь внутри подпроцесса. Только ОП08 меняет деньги; отмена и повтор не проводят их заново.'),
 ('V5_loans','Кредитный специалист','Проверить условия\nи даты платежей','Проверить полномочия\nи допустимость условий','Рассчитать план;\nсохранить договор\nи все строки атомарно','Получить договор\nи согласованный план',['ОП10'],['ОП11'],['ДО6 / ДО7\nУсловия и план','Д4; Д5\nДоговор и аудит'],'ОП11 использует расчёт М07 и сохранение М06. План не заменяет сведения о фактической выдаче и оплате.'),
 ('V6_reports','Получатель сведений по роли','Выбрать документ,\nпериод и вид контроля','Проверить полномочия\nи границы периода','Выдать результат /\nсвести факты /\nвыполнить сверку','Оценить результат\nпо исходным документам',[],['ОП13','ОП14','ОП15'],['ДО9\nЗапрос и документ','Д1–Д5\nПодтверждённые факты'],'Вид запроса выбирает ОП13/ОП14/ОП15. Представление не меняет предметные записи; период и актуальность входят в результат.'),
 ('V8_reference','Администратор','Передать изменения\nотделения или сотрудника','Проверить роль,\nдубли и допустимые поля','Сохранить справочник\nили активность;\nзаписать аудит','Получить ID, реквизиты\nлибо причину отказа',[],['ОП03'],['ДО2\nСправочник','Д1; Д5\nРеквизиты и аудит'],'Администратор приложения не получает право проводить деньги или править аудит.'),
 ('V9_close','Кредитный специалист','Предъявить основание\nзакрытия договора','Проверить роль,\nдоговор и close_ref','Установить closed;\nсохранить основание\nи аудит','Получить подтверждение\nи исходный план',[],['ОП12'],['ДО8\nПодтверждение расчётов','Д4; Д5\nИстория договора'],'ОП12 не переписывает условия и график. Фактическое исполнение подтверждено кредитной службой до команды.'),
]

def data(s,x,title,nodeid,store=False):
 y=685;w=250;h=88
 if store:
  s.add(f'<path d="M{x},{y+15} C{x},{y-5} {x+w},{y-5} {x+w},{y+15} V{y+h-15} C{x+w},{y+h+5} {x},{y+h+5} {x},{y+h-15} Z" fill="{GREEN}" stroke="black" stroke-width="2"/>')
  s.add(f'<ellipse cx="{x+w/2}" cy="{y+15}" rx="{w/2}" ry="15" fill="none" stroke="black" stroke-width="2"/>')
 else:
  s.add(f'<path d="M{x},{y} H{x+w-18} L{x+w},{y+18} V{y+h} H{x} Z M{x+w-18},{y} V{y+18} H{x+w}" fill="white" stroke="black" stroke-width="2"/>')
 s.text(x+w/2,y+h/2+7,title,21,w-24)
 nx,ny,nw,nh=s.nodes[nodeid]
 pts=[(nx+nw/2,ny+nh),(x+w/2,y)]
 if not store:pts.reverse()
 s.add('<polyline points="'+' '.join(f'{xx},{yy}' for xx,yy in pts)+'" fill="none" stroke="black" stroke-width="1.6" stroke-dasharray="4 5" marker-end="url(#dataArrow)"/>')
 s.data_count+=1
 if store:s.data_outputs+=1
 else:s.data_inputs+=1

class PortraitProcess(BPMN):
 """Две вертикальные дорожки, читаемые на книжном листе A4."""
 def __init__(self,name,role):
  Picture.__init__(self,name,1500,1800)
  self.nodes={};self.seq=[];self.kinds={};self.operations=set()
  self.data_count=0;self.data_inputs=0;self.data_outputs=0;self._footer=False
  self.add('<rect x="90" y="25" width="1400" height="1585" fill="white" stroke="black" stroke-width="2"/>')
  self.add('<rect x="720" y="105" width="770" height="1505" fill="#F7F7F7"/>')
  self.line([(90,105),(1490,105)]);self.line([(720,25),(720,1610)])
  self.text(405,65,role,32,590);self.text(1105,65,'Банковская система',32,680)
  self.add('<defs><marker id="dataArrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M1,1 L9,5 L1,9" fill="none" stroke="black" stroke-width="1.4"/></marker></defs>')

 def text(self,x,y,text,size=30,maxw=None,anchor='middle',bold=False,bg=False):
  # Сохраняем общую проверку связности BPMN.finish и раздвигаем его подписи.
  if self._footer:y=self.h-148 if y==self.h-66 else self.h-60
  return super().text(x,y,text,max(size,30),maxw,anchor,bold,bg)

 def task_at(self,key,x,y,text,w=490,h=150,human=False,sub=False,ops=()):
  self.filled(x,y,w,h,fill=YELLOW if human else BLUE,round=True)
  if sub:
   if ops:self.text(x+w/2,y+30,', '.join(ops),30,w-24)
   self.text(x+w/2,y+(h-32)/2+(18 if ops else 0),text,30,w-32)
   self.box(x+w/2-15,y+h-34,30,30);self.text(x+w/2,y+h-19,'+',30)
  else:self.text(x+w/2,y+h/2,text,30,w-32)
  if ops and not sub:self.text(x+w/2,y-28,', '.join(ops),30,w-24,bg=True)
  self.nodes[key]=(x,y,w,h);self.kinds[key]='task';self.operations.update(ops)

 def gate_at(self,key,cy,label):
  self.box(1065,cy-40,80,80,'×',38,'diamond')
  self.text(1290,cy,label,30,260)
  self.nodes[key]=(1065,cy-40,80,80);self.kinds[key]='gateway'

 def event_at(self,key,cy,label,end=False):
  self.circle(405,cy,28,thick=end);self.text(550,cy,label,30,230)
  self.nodes[key]=(377,cy-28,56,56);self.kinds[key]='end' if end else 'start'

 def data_at(self,x,y,w,h,title,target,store=False):
  if store:
   self.add(f'<path d="M{x},{y+18} C{x},{y-6} {x+w},{y-6} {x+w},{y+18} V{y+h-18} C{x+w},{y+h+6} {x},{y+h+6} {x},{y+h-18} Z" fill="{GREEN}" stroke="black" stroke-width="2"/>')
   self.add(f'<ellipse cx="{x+w/2}" cy="{y+18}" rx="{w/2}" ry="18" fill="none" stroke="black" stroke-width="2"/>')
   tx,ty,tw,th=self.nodes[target]
   pts=[(tx+tw,ty+th/2),(1445,ty+th/2),(1445,1410),(x+w/2,1410),(x+w/2,y)]
  else:
   self.add(f'<path d="M{x},{y} H{x+w-24} L{x+w},{y+24} V{y+h} H{x} Z M{x+w-24},{y} V{y+24} H{x+w}" fill="white" stroke="black" stroke-width="2"/>')
   tx,ty,tw,th=self.nodes[target]
   pts=[(x+w,y+h/2),(760,y+h/2),(760,ty+th/2),(tx,ty+th/2)]
  self.text(x+w/2,y+h/2+8,title,30,w-32)
  self.add('<polyline points="'+' '.join(f'{a},{b}' for a,b in pts)+'" fill="none" stroke="black" stroke-width="1.8" stroke-dasharray="5 6" marker-end="url(#dataArrow)"/>')
  self.data_count+=1
  if store:self.data_outputs+=1
  else:self.data_inputs+=1

 def finish(self,note=''):
  self._footer=True
  try:return super().finish(note)
  finally:self._footer=False


def process(spec):
 name,role,command,check,operation,result,check_ops,op_ops,docs,note=spec
 s=PortraitProcess(name,role)
 s.event_at('s',145,'Обращение');s.task_at('cmd',160,200,command,h=140,human=True)
 s.task_at('check',810,430,check,w=590,h=150,ops=check_ops)
 s.gate_at('allow',700,'Допустимо?')
 s.task_at('op',810,855,operation,w=590,h=220,sub=True,ops=op_ops)
 s.gate_at('ok',1210,'Успешно?')
 s.task_at('result',160,1330,result,human=True);s.event_at('e',1560,'Завершено',True)
 s.task_at('error',160,780,'Прочитать отказ\nи текущее состояние',h=160,human=True);s.event_at('no',1100,'Отклонено',True)
 s.link('s','cmd',source='bottom',target='top')
 s.link('cmd','check',source='right',target='top',route=[(740,270),(740,385),(1105,385)])
 s.link('check','allow',source='bottom',target='top')
 s.link('allow','op','да',source='bottom',target='top',labelpos=(1150,790))
 s.link('op','ok',source='bottom',target='top')
 s.link('ok','result','да',source='bottom',target='right',route=[(1105,1330),(700,1330),(700,1405)],labelpos=(1150,1290))
 s.link('result','e',source='bottom',target='top');s.link('error','no',source='bottom',target='top')
 s.link('allow','error','нет',source='left',target='top',route=[(760,700),(405,700)],labelpos=(800,667))
 s.link('ok','error','нет',source='left',target='right',route=[(760,1210),(760,860)],labelpos=(940,1175))
 s.data_at(160,430,490,125,docs[0],'check')
 s.data_at(835,1450,540,130,docs[1],'op',True)
 return s.finish(note)

def all_processes():
 from detailed_process_figures import BUILDERS
 return [BUILDERS[spec[0]]() if spec[0] in BUILDERS else process(spec) for spec in SPECS]
