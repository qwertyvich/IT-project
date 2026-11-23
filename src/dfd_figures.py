import html
from diagram_tools import Graph,Picture,BLUE,YELLOW,GREEN,q,wrap
from dfd_model import *

def safe(id):return id.replace('.','_')
def node(g,id):
 key=safe(id)
 if id in ACTORS:g.node(key,id+'\n'+ACTORS[id])
 elif id in STORES:
  # Gane–Sarson store: identifier compartment and a body open on the right.
  g.nodes.add(key)
  title='<BR/>'.join(html.escape(x) for x in wrap(STORES[id]).split('\n'))
  label=f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="7"><TR><TD BORDER="1" SIDES="TLBR" BGCOLOR="{GREEN}">{id}</TD><TD BORDER="1" SIDES="TB" BGCOLOR="{GREEN}">{title}</TD></TR></TABLE>'
  g.body.append(q(key)+' [shape=plain,style="",label=<'+label+'>];')
 elif id in TITLES:g.node(key,id+'\n'+TITLES[id],'box',YELLOW,style='rounded,filled')
 else:g.node(key,id+'\n'+LEAF_TITLES[id],'box',YELLOW,style='rounded,filled')

def context():
 g=Graph('B1_context','LR',22);g.node('P0','0\nОбеспечивать согласованный\nоперационный учёт банка','box',YELLOW,style='rounded,filled')
 for id in ACTORS:node(g,id)
 for id,a,b,name,_ in FLOWS:
  if id.startswith('F'):g.edge(a if a in ACTORS else 'P0',b if b in ACTORS else 'P0',id+' '+name)
 return g.save()

def level_one():
 g=Graph('B2_dfd','LR',23)
 g.body.append('graph [nodesep=.6, ranksep=1.1];')
 used=set()
 for id,a,b,name,_ in FLOWS:
  if not id.startswith(('F','I')):continue
  aa=a+'_out' if a in ACTORS and b in TITLES else a
  bb=b+'_in' if b in ACTORS and a in TITLES else b
  for x,original in [(aa,a),(bb,b)]:
   if x in used:continue
   used.add(x)
   if original in ACTORS:g.node(x,original+'\n'+ACTORS[original])
   else:node(g,x)
  g.edge(aa,bb,id+' '+name)
 g.body.append('{rank=same; F2; F3; F4;}')
 return g.save()

def resource_view():
 g=Graph('B9_resources','LR',22)
 for id in TITLES:node(g,id)
 for id in STORES:node(g,id)
 for id,a,b,name,_ in FLOWS:
  if id.startswith(('R','W')):g.edge(a,b,id+' '+name)
 return g.save()

def detail(parent):
 g=Graph(NAMES[parent],'LR',21);used=set()
 for a,b,id,name in detail_edges(parent):
  for x in (a,b):
   if x not in used:node(g,x);used.add(x)
  # The typed flow dictionary supplies the full field composition.
  g.edge(safe(a),safe(b),id+' '+name)
 if parent=='F5':
  # Layout-only links place the independent result leaves across the sheet.
  g.edge('F5_1','F5_2',style='invis',weight='8')
  g.edge('F5_2','F5_3',style='invis',weight='8')
 return g.save()

def all_figures():
 validate_dfd()
 return [context(),level_one()]+[detail(p) for p in TITLES]+[resource_view()]
