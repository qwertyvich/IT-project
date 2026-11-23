"""Расчёт проектных критериев. Демонстрационные числа не являются испытаниями банка."""
from decimal import Decimal

def decision(a=None,b=None,qa=None,qb=None,*,same_staff=None,complete_logs=None,max_b_seconds=None,critical=None):
 # Критическое нарушение нельзя компенсировать или скрыть отсутствующим замером.
 if critical is not None and critical>0:return {'verdict':'не соответствует','reason':'критическое нарушение'}
 if None in (a,b,qa,qb,same_staff,complete_logs,max_b_seconds,critical):
  return {'verdict':'недостаточно свидетельств'}
 if not complete_logs or not same_staff:return {'verdict':'недостаточно свидетельств'}
 if qa!=30:return {'verdict':'недостаточно свидетельств','reason':'неподтверждённая база сравнения'}
 if qb!=30 or max_b_seconds>120:return {'verdict':'не соответствует','reason':'не достигнута полнота или оперативность'}
 a,b=Decimal(str(a)),Decimal(str(b))
 if a<=0 or b<0:return {'verdict':'недостаточно свидетельств'}
 ua,ub=a/qa,b/qb
 reduction=(ua-ub)/ua*100
 return {'verdict':'соответствует' if ub<=Decimal('.80')*ua else 'не соответствует','u_a':str(ua),'u_b':str(ub),'reduction_percent':str(reduction)}

def check_reference():
 args=dict(qa=30,qb=30,same_staff=True,complete_logs=True,max_b_seconds=120,critical=0)
 r=decision(180,135,**args);assert r['verdict']=='соответствует' and Decimal(r['reduction_percent'])==25
 assert decision(180,145,**args)['verdict']=='не соответствует'
 assert decision(180,135,**{**args,'critical':1})['verdict']=='не соответствует'
 assert decision(None,135,**args)['verdict']=='недостаточно свидетельств'
 assert decision(180,135,**{**args,'complete_logs':False})['verdict']=='недостаточно свидетельств'
 assert decision(180,135,**{**args,'qb':29})['verdict']=='не соответствует'
 assert decision(180,135,**{**args,'qa':29})['verdict']=='недостаточно свидетельств'
 return {'synthetic_formula_reference':r,'boundary_cases':7,'bank_software_trials':False}
