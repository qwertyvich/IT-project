"""Концептуальная ER-модель в нотации Чена, согласованная с 12 FK.

Повторения сущностей в четырёх фрагментах нужны только для компоновки.
Полный состав полей остаётся на отдельной логической ER-диаграмме.
"""
import hashlib
import math
from pathlib import Path

from diagram_tools import Picture
from project_model import FIG, ENTITIES, FK


def chen_model(out_dir=FIG / 'concise'):
    s = Picture('C_A0_chen', 3400, 2340)
    entities = {}
    relationships = []
    attributes = []

    def text(x, y, value, size=36, maxw=600, bold=False):
        return s.text(x, y, value, size, maxw, bold=bold)

    def line(points, double=False):
        if not double:
            s.line(points, False, width=2.5)
            return
        # Параллельные полилинии с общими углами показывают полное участие.
        normals = []
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            length = math.hypot(x2-x1, y2-y1)
            normals.append((-(y2-y1)/length, (x2-x1)/length))
        for sign in (-1, 1):
            shifted = []
            for i, (x, y) in enumerate(points):
                ns = normals[max(0, i-1):min(len(normals), i+1)]
                nx, ny = (sum(n[j] for n in ns)/len(ns) for j in (0, 1))
                shifted.append((x+sign*5*nx, y+sign*5*ny))
            s.line(shifted, False, width=2.5)

    def entity(alias, model, x, y, weak=False):
        title = next(title for name, title, _ in ENTITIES if name == model)
        w, h = 350, 100
        s.filled(x-w/2, y-h/2, w, h, fill='white')
        if weak:
            s.filled(x-w/2+8, y-h/2+8, w-16, h-16, fill='white')
        text(x, y, title, maxw=w-26, bold=True)
        entities[alias] = (model, x, y)

    def attribute(alias, field, title, x, y, key=False, partial=False):
        assert 0 <= x-140 and x+140 <= s.w and 0 <= y-42 and y+42 <= s.h
        model, ex, ey = entities[alias]
        fields = {f[0] for name, _, fs in ENTITIES if name == model for f in fs}
        assert field in fields, (model, field)
        # Обрезать соединение по границам эллипса и прямоугольника.
        dx, dy = x-ex, y-ey
        t1 = min(175/abs(dx) if dx else float('inf'), 50/abs(dy) if dy else float('inf'))
        t2 = 1/math.sqrt((dx/140)**2+(dy/42)**2)
        line([(ex+dx*t1, ey+dy*t1), (x-dx*t2, y-dy*t2)])
        s.add(f'<ellipse cx="{x}" cy="{y}" rx="140" ry="42" fill="white" stroke="black" stroke-width="2.5"/>')
        text(x, y, title, maxw=262)
        if key or partial:
            length = min(240, len(title)*19)
            dash = ' stroke-dasharray="10 6"' if partial else ''
            s.add(f'<path d="M {x-length/2} {y+23} H {x+length/2}" stroke="black" stroke-width="2"{dash}/>')
        attributes.append({'entity': model, 'field': field, 'key': key, 'partial_key': partial})

    def relation(child, field, parent, title, x, y, parent_points, child_points,
                 parent_label, child_label, identifying=False):
        child_model, _, _ = entities[child]
        parent_model, _, _ = entities[parent]
        target = next(k for a, f, b, k in FK if (a, f, b) == (child_model, field, parent_model))
        line(parent_points, double=identifying)
        line(child_points, double=True)
        w, h = 250, 134
        def diamond(inset=0):
            s.add(f'<polygon points="{x},{y-h/2+inset} {x+w/2-inset},{y} {x},{y+h/2-inset} {x-w/2+inset},{y}" fill="white" stroke="black" stroke-width="2.5"/>')
        diamond()
        if identifying:
            diamond(9)
        text(x, y, title, maxw=200)
        for (lx, ly), label in [(parent_label, '1'), (child_label, 'N')]:
            s.text(lx, ly, label, 36, 100, bg=True)
        relationships.append({'from': child_model, 'field': field, 'to': parent_model, 'target': target})

    # Рамки отделяют фрагменты одной модели; они не являются сущностями.
    for x, y, title in [(25, 45, 'Клиенты, счета и сотрудники'),
                         (1680, 45, 'Карты и внутрибанковские переводы'),
                         (25, 1140, 'Кредитный договор и план'),
                         (1680, 1140, 'Служебный аудит')]:
        width = 1710 if x == 1680 else 1640
        s.add(f'<rect x="{x}" y="{y}" width="{width}" height="1040" fill="none" stroke="#777" stroke-width="2" stroke-dasharray="12 8"/>')
        text(x+width/2, y+48, title, 40, width-60, True)

    entity('client', 'client', 310, 370)
    entity('account', 'account', 1300, 370)
    entity('branch', 'branch', 1300, 820)
    entity('employee', 'employee', 310, 820)
    relation('account', 'client_id', 'client', 'владеет', 805, 370,
             [(485,370),(680,370)], [(930,370),(1125,370)], (545,330), (1070,330))
    relation('account', 'branch_id', 'branch', 'обслужи-\nвает', 1300, 595,
             [(1300,770),(1300,662)], [(1300,528),(1300,420)], (1350,715), (1350,475))
    relation('employee', 'branch_id', 'branch', 'работает\nв', 805, 820,
             [(1125,820),(930,820)], [(680,820),(485,820)], (1070,780), (545,780))
    for alias, values in {
        'client': [('client_id','ID клиента',180,190,True),('full_name','ФИО',490,190,False)],
        'account': [('account_id','ID счёта',1140,190,True),('account_number','Номер',1450,190,False)],
        'branch': [('branch_id','ID отделения',1140,1000,True),('branch_code','Код',1450,1000,False)],
        'employee': [('employee_id','ID сотрудника',180,1000,True),('role_code','Роль',490,1000,False)],
    }.items():
        for field, title, x, y, key in values:
            attribute(alias, field, title, x, y, key=key)

    entity('account_t', 'account', 1985, 370)
    entity('card', 'bank_card', 3130, 370)
    entity('transfer', 'transfer', 1985, 820)
    entity('employee_t', 'employee', 3130, 820)
    relation('card', 'account_id', 'account_t', 'имеет\nкарту', 2555, 370,
             [(2160,370),(2430,370)], [(2680,370),(2955,370)], (2240,330), (2880,330))
    relation('transfer', 'from_account_id', 'account_t', 'списа-\nние', 1865, 595,
             [(1895,420),(1865,465),(1865,528)], [(1865,662),(1865,715),(1895,770)], (1815,465), (1815,720))
    relation('transfer', 'to_account_id', 'account_t', 'зачис-\nление', 2160, 595,
             [(2075,420),(2160,465),(2160,528)], [(2160,662),(2160,715),(2075,770)], (2220,465), (2220,720))
    relation('card', 'issued_by', 'employee_t', 'регист-\nрирует', 3130, 595,
             [(3130,770),(3130,662)], [(3130,528),(3130,420)], (3180,715), (3180,475))
    relation('transfer', 'created_by', 'employee_t', 'создаёт', 2555, 820,
             [(2955,820),(2680,820)], [(2430,820),(2160,820)], (2880,780), (2240,780))
    for alias, field, title, x, y, key in [
        ('account_t','account_id','ID счёта',1850,190,True), ('account_t','account_number','Номер',2160,190,False),
        ('card','card_id','ID карты',2925,190,True), ('card','card_number','Номер',3235,190,False),
        ('transfer','transfer_id','ID перевода',1850,1000,True), ('transfer','amount','Сумма',2160,1000,False),
        ('employee_t','employee_id','ID сотрудника',2925,1000,True), ('employee_t','role_code','Роль',3235,1000,False),
    ]:
        attribute(alias, field, title, x, y, key=key)

    entity('account_l', 'account', 310, 1450)
    entity('loan', 'loan', 1300, 1450)
    entity('employee_l', 'employee', 310, 1930)
    entity('payment', 'loan_schedule', 1300, 1930, weak=True)
    relation('loan', 'account_id', 'account_l', 'относится\nк счёту', 805, 1450,
             [(485,1450),(680,1450)], [(930,1450),(1125,1450)], (545,1410), (1070,1410))
    relation('loan', 'created_by', 'employee_l', 'регист-\nрирует', 805, 1740,
             [(485,1930),(590,1930),(590,1740),(680,1740)],
             [(930,1740),(1120,1740),(1120,1560),(1170,1500)], (545,1890), (1080,1620))
    relation('payment', 'loan_id', 'loan', 'содержит', 1300, 1690,
             [(1300,1500),(1300,1623)], [(1300,1757),(1300,1880)], (1350,1560), (1350,1815), identifying=True)
    for alias, field, title, x, y, key in [
        ('account_l','account_id','ID счёта',180,1270,True), ('account_l','account_number','Номер',490,1270,False),
        ('loan','loan_id','ID договора',1140,1270,True), ('loan','contract_ref','Номер договора',1450,1270,False),
        ('employee_l','employee_id','ID сотрудника',180,2110,True), ('employee_l','role_code','Роль',490,2110,False),
        ('payment','due_on','Дата платежа',1450,2110,False),
    ]:
        attribute(alias, field, title, x, y, key=key)
    attribute('payment', 'payment_no', '№ платежа', 1140, 2110, partial=True)

    entity('employee_a', 'employee', 2050, 1450)
    entity('event', 'audit_event', 3100, 1450)
    relation('event', 'actor_id', 'employee_a', 'совершает', 2575, 1450,
             [(2225,1450),(2450,1450)], [(2700,1450),(2925,1450)], (2290,1410), (2860,1410))
    for alias, field, title, x, y, key in [
        ('employee_a','employee_id','ID сотрудника',1890,1270,True), ('employee_a','role_code','Роль',2200,1270,False),
        ('event','event_id','ID события',2925,1270,True), ('event','action','Действие',3235,1270,False),
        ('event','entity_type','Тип объекта',2940,1670,False), ('event','entity_id','ID объекта',3230,1670,False),
        ('event','occurred_at','Время',2650,1670,False),
    ]:
        attribute(alias, field, title, x, y, key=key)
    text(2555, 2000, 'Тип и ID объекта задают предмет аудита;', maxw=1530)
    text(2555, 2050, 'универсальная FK-связь с ним не вводится.', maxw=1530)

    text(1700, 2210, 'Прямоугольник — сущность; ромб — связь; овал — атрибут; подчёркнутый атрибут — ключ. 1:N — кратность.', maxw=3310)
    text(1700, 2260, 'Двойная линия — обязательное участие; двойные рамки — слабая сущность и идентифицирующая связь; пунктир — частичный ключ.', maxw=3310)
    text(1700, 2310, 'Повторённые сущности во фрагментах тождественны. Показаны основные атрибуты; полный состав и типы — на логической ER-модели.', maxw=3310)

    expected = {(a, f, b, k) for a, f, b, k in FK}
    actual = {(r['from'], r['field'], r['to'], r['target']) for r in relationships}
    assert actual == expected and len(relationships) == 12
    assert {model for model, _, _ in entities.values()} == {e[0] for e in ENTITIES}
    assert all(0 <= x and 0 <= y and x+w <= s.w and y+h <= s.h for x,y,w,h in s.boxes)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{s.w}" height="{s.h}" viewBox="0 0 {s.w} {s.h}">'
           '<rect width="100%" height="100%" fill="white"/>' + '\n'.join(s.parts) + '</svg>')
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / (s.name+'.svg')
    path.write_text(svg, encoding='utf-8')
    return {'name': s.name, 'source': 'svg', 'width': s.w, 'height': s.h,
            'entities': 9, 'relationships': relationships, 'attributes': attributes,
            'notation': 'Чен: сущности, связи, атрибуты, ключи и обязательное участие',
            'sha256_svg': hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == '__main__':
    chen_model()
