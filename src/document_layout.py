"""Сборка пояснительной записки и материалов защиты в DOCX."""
from pathlib import Path
from copy import deepcopy
import json, re, shutil, hashlib
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from project_model import *


class Writer:
    def __init__(self,compact=False):
        self.compact=compact;self.cover_stage=compact
        self.doc=Document();self.tables=0;self.figures=0;self.app_letter=None;self.app_tables={};self.pending_break=False;self.flow=False;self.after_table=False
        self.setup(self.doc.sections[0],False,first=True)
        self.styles()
        self.doc.core_properties.title=TOPIC
        self.doc.core_properties.subject='Технический проект и программа испытаний'
        self.doc.core_properties.author=AUTHOR
        self.doc.core_properties.last_modified_by=AUTHOR
        self.doc.core_properties.comments=''
        sett=self.doc.settings.element
        u=OxmlElement('w:updateFields');u.set(qn('w:val'),'true');sett.append(u)
        auto=OxmlElement('w:doNotAutoHyphenate');sett.append(auto)
    def setup(self,s,landscape=False,first=False,a3=False):
        s.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
        s.page_width=Mm(420 if a3 else (297 if landscape else 210));s.page_height=Mm(297 if a3 else (210 if landscape else 297))
        s.left_margin=Mm(30);s.right_margin=Mm(15);s.top_margin=Mm(20);s.bottom_margin=Mm(20)
        s.header_distance=Mm(8);s.footer_distance=Mm(10)
        s.different_first_page_header_footer=first
        if first:
            p=s.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent=Mm(0)
            r=p.add_run();r.font.name='Times New Roman';r.font.size=Pt(12)
            field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');r._r.addnext(field)
    def styles(self):
        d=self.doc
        for st in d.styles:
            if st.type in (1,2):
                st.font.name='Times New Roman';st.font.size=Pt(14);st.font.color.rgb=RGBColor(0,0,0)
                rf=st.element.get_or_add_rPr();fonts=rf.find(qn('w:rFonts'))
                if fonts is None:fonts=OxmlElement('w:rFonts');rf.insert(0,fonts)
                for key in list(fonts.attrib):
                    if 'theme' in key.lower():del fonts.attrib[key]
                for key in ('ascii','hAnsi','cs','eastAsia'):fonts.set(qn('w:'+key),'Times New Roman')
                for border in st.element.xpath('.//w:pBdr'):border.getparent().remove(border)
                for color in st.element.xpath('.//w:color'):
                    for key in list(color.attrib):
                        if 'theme' in key.lower():del color.attrib[key]
        normal=d.styles['Normal'];normal.font.size=Pt(12 if self.compact else 14);pf=normal.paragraph_format
        pf.first_line_indent=Mm(12.5);pf.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.line_spacing=1.5;pf.space_before=Pt(0);pf.space_after=Pt(0);pf.widow_control=True;pf.keep_with_next=False
        for name in ('Heading 1','Heading 2','Heading 3'):
            st=d.styles[name];st.font.bold=True;st.font.size=Pt(14)
            pf=st.paragraph_format;pf.first_line_indent=Mm(12.5);pf.left_indent=Mm(0)
            pf.space_before=Pt(10);pf.space_after=Pt(6);pf.line_spacing=1.5;pf.keep_with_next=True;pf.keep_together=True
        title=d.styles['Title'];title.font.name='Times New Roman';title.font.size=Pt(16);title.font.bold=True
        title.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER;title.paragraph_format.first_line_indent=Mm(0)
        title.paragraph_format.space_after=Pt(10);title.paragraph_format.line_spacing=1.5
        for name in ('TOC 1','TOC 2','TOC 3'):
            try:st=d.styles[name]
            except KeyError:st=d.styles.add_style(name,1)
            st.font.size=Pt(12);st.font.bold=False
            st.paragraph_format.first_line_indent=Mm(0);st.paragraph_format.line_spacing=1.15
            st.paragraph_format.space_after=Pt(4)
        for name in ('Caption',):
            st=d.styles[name];st.font.size=Pt(12);st.font.italic=False;st.font.bold=False
            st.paragraph_format.line_spacing=1.15;st.paragraph_format.first_line_indent=Mm(0)
    def p(self,text='',style=None,align=None,size=None,indent=None,before=0,after=0,keep=None):
        if self.cover_stage and style!='Title' and size is None:size=14
        p=self.doc.add_paragraph(style=style)
        if self.pending_break:p.paragraph_format.page_break_before=True;self.pending_break=False
        if self.after_table:before=max(before,5);self.after_table=False
        if text:p.add_run(text)
        if align is not None:p.alignment=align
        if size:
            for r in p.runs:r.font.size=Pt(size)
        if indent is not None:p.paragraph_format.first_line_indent=Mm(indent)
        p.paragraph_format.space_before=Pt(before);p.paragraph_format.space_after=Pt(after)
        if keep is not None:p.paragraph_format.keep_with_next=keep
        return p
    def h(self,text,level=2):return self.p(text,f'Heading {level}')
    def structural(self,text,new=True):
        if text=='РЕФЕРАТ':self.cover_stage=False
        if new:self.br()
        if text in ('РЕФЕРАТ','СОДЕРЖАНИЕ'):
            p=self.p(text,align=WD_ALIGN_PARAGRAPH.CENTER,indent=0,after=12)
            p.runs[0].font.bold=True
        else:p=self.p(text,'Heading 1',WD_ALIGN_PARAGRAPH.CENTER,indent=0,after=12)
        return p
    def br(self):
        self.pending_break=True
    def page(self,title=None,level=2):
        if level==1 or not self.flow:self.br()
        if title:self.h(title,level)
    def table(self,caption,headers,rows,widths=None,size=None):
        size=size or (11 if self.compact else 12)
        self.tables+=1
        if self.app_letter:
            self.app_tables[self.app_letter]=self.app_tables.get(self.app_letter,0)+1
            number=f'{self.app_letter}.{self.app_tables[self.app_letter]}'
        else:number=str(self.tables)
        references={
          'Деятельность, система и программный продукт':'Границы деятельности, системы и программного продукта сопоставлены',
          'Роли и результаты работы':'Распределение обязанностей и результатов приведено',
          'Правила предметной области':'Ограничения допустимых состояний перечислены',
          'Группы требований':'Группы требований сопоставлены с примерами проверок',
          'Функции и информационные ресурсы':'Соответствие функций и информационных ресурсов показано',
          'Заинтересованные стороны и архитектурные представления':'Интересы сторон и соответствующие архитектурные решения сопоставлены',
          'Показатели качества и правила принятия':'Показатели и обязательные критерии качества приведены',
          'Распределение контроля целостности':'Распределение правил между механизмами контроля показано',
          'Контрольные состояния проведения':'Эталонные денежные состояния приведены',
          'Состав запросов':'Назначение и построение запросов определены',
          'Основные контракты API':'Входы и результаты основных операций API приведены',
          'План индивидуальной реализации':'Планируемые этапы и результаты реализации перечислены',
          'Матрица прослеживаемости':'Связи требований, функций, компонентов и проверок представлены',
          'Средства испытаний':'Средства испытаний и условия их применения определены',
          'Контрольные факты и ожидаемая аналитика':'Контрольные факты и вычисленные эталонные результаты представлены',
          'Форма записи результата':'Состав записи протокола испытания показан',
        }
        tx=references.get(caption)
        if tx is None:
            name=caption.lower()
            groups=[
                (('критери','свойства','качеств'),'Показатели и условия оценки приведены'),
                (('гипотез','проблем'),'Проблемы обслуживания и проверяемые решения сопоставлены'),
                (('требован','прослеживаем'),'Требования и связанные проверки приведены'),
                (('поток','лексем'),'Состав информации и связи данных определены'),
                (('операци','лист','средств исполнения'),'Операции и условия их программного исполнения представлены'),
                (('контракт','интерфейс','отказ'),'Условия взаимодействия и обработки результатов определены'),
                (('сотрудник','участник','сторон'),'Обязанности и потребности участников приведены'),
                (('принцип','развити'),'Принципы работы и изменения системы приведены'),
                (('компонент','реализац'),'Ответственность программных средств определена'),
                (('испытан','наблюден','протокол'),'Условия проведения и регистрации проверки приведены'),
                (('запрос','отчёт'),'Состав запросов и ожидаемых сведений определён'),
                (('документ','ограничен'),'Документы и условия обработки сведений приведены'),
                (('результат','траектори'),'Ожидаемые результаты обработки представлены'),
            ]
            tx=next((text for keys,text in groups if any(k in name for k in keys)),None)
            if any(caption.endswith(' '+name) for name,_,_ in ENTITIES):
                tx='Атрибуты, типы и ограничения отношения приведены'
            if tx is None:tx='Состав и характеристики данных приведены'
        # Приложение содержит общую ссылку на диапазон своих таблиц.
        # Не повторяем перед каждой спецификацией отдельную вводную строку.
        if not self.app_letter:self.p(f'{tx} в таблице {number}.',keep=True,before=4)
        cap=self.p(f'Таблица {number} — {caption}',indent=0,size=12,before=5,after=3,keep=True)
        cap.paragraph_format.line_spacing=1.15
        t=self.doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
        if widths:
            for c,w in zip(t.columns,widths):c.width=Mm(w)
        tp=t._tbl.tblPr
        borders=OxmlElement('w:tblBorders')
        for key in ('top','left','bottom','right','insideH','insideV'):
            b=OxmlElement('w:'+key);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'000000');borders.append(b)
        tp.append(borders)
        mar=OxmlElement('w:tblCellMar')
        for key,val in [('top',70),('bottom',70),('left',85),('right',85)]:
            b=OxmlElement('w:'+key);b.set(qn('w:w'),str(val));b.set(qn('w:type'),'dxa');mar.append(b)
        tp.append(mar)
        for i,rowdata in enumerate([headers]+list(rows)):
            cells=t.rows[0].cells if i==0 else t.add_row().cells
            if i==0:
                repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
            for j,(c,tx) in enumerate(zip(cells,rowdata)):
                if widths:c.width=Mm(widths[j])
                c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p=c.paragraphs[0];p.paragraph_format.first_line_indent=Mm(0);p.paragraph_format.space_after=Pt(0)
                p.paragraph_format.line_spacing=1.0;p.paragraph_format.keep_with_next=(i==0)
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER if i==0 or (j==0 and len(str(tx))<14) else WD_ALIGN_PARAGRAPH.LEFT
                r=p.add_run(str(tx));r.font.name='Times New Roman';r.font.size=Pt(size);r.font.bold=False
                if i==0:
                    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'F2F2F2');c._tc.get_or_add_tcPr().append(shade)
            nr=OxmlElement('w:cantSplit');t.rows[i]._tr.get_or_add_trPr().append(nr)
        self.after_table=True
        return t
    def section(self,landscape=False,a3=False):
        self.pending_break=False;self.after_table=False
        s=self.doc.add_section(WD_SECTION_START.NEW_PAGE);self.setup(s,landscape,first=False,a3=a3)
        return s
    def figure(self,filename,caption,max_height_mm=None):
        self.figures+=1
        pic=FIG/(filename+'.png')
        from PIL import Image
        with Image.open(pic) as im:w,h=im.size
        sec=self.doc.sections[-1]
        maxw=sec.page_width-sec.left_margin-sec.right_margin
        # 135 mm for landscape figures leaves room for section label, caption and explanation.
        maxh=Mm(max_height_mm or (220 if sec.page_width.mm>400 else (145 if sec.orientation==WD_ORIENT.LANDSCAPE else 225)))
        width=min(maxw,int(maxh*w/h))
        p=self.p('',align=WD_ALIGN_PARAGRAPH.CENTER,indent=0,keep=True)
        p.paragraph_format.line_spacing=1.0
        r=p.add_run();r.add_picture(str(pic),width=width)
        drawing=r._r.xpath('.//wp:docPr')[0];drawing.set('descr',caption)
        p=self.p(caption,'Caption',WD_ALIGN_PARAGRAPH.CENTER,indent=0,after=3)
        return p
    def save(self,path):self.doc.save(path)
