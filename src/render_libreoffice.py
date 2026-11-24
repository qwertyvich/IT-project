"""Обновить поля и TOC, выгрузить PDF/A и карту строк через LibreOffice.

Изолированный временный профиль содержит только созданный здесь макрос.
Word-сборка остаётся доступна через render_word.ps1. Нужен путь к soffice.
"""
import argparse
import html
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


def render(soffice, document, pdf, table_map=None):
    document, pdf = Path(document).resolve(), Path(pdf).resolve()
    pdf.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='bank-lo-') as temporary:
        profile = Path(temporary)
        subprocess.run([str(soffice), '--headless', '--nologo',
                        '-env:UserInstallation='+profile.as_uri(), '--terminate_after_init'],
                       check=True, timeout=30)
        basic = profile / 'user/basic'
        standard = basic / 'Standard'
        standard.mkdir(parents=True, exist_ok=True)
        (basic/'script.xlc').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<library:libraries xmlns:library="http://openoffice.org/2000/library"><library:library library:name="Standard" library:link="false"/></library:libraries>''')
        (standard/'script.xlb').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<library:library xmlns:library="http://openoffice.org/2000/library" library:name="Standard" library:readonly="false" library:passwordprotected="false"><library:element library:name="Module1"/></library:library>''')
        receipt = profile/'receipt.txt'
        mapping = profile/'tables.json'
        source = '''Option Explicit
Function Prop(n, v)
 Dim p As New com.sun.star.beans.PropertyValue
 p.Name = n
 p.Value = v
 Prop = p
End Function
Sub Main
 On Error GoTo Failed
 Dim doc, indexes, idx, finder, found, cursor, styles, st, name, vc
 Dim i As Long, j As Long, k As Long, firstPage As Long, lastPage As Long
 Dim table, cell, f As Integer, result As String, rowText As String
 doc = StarDesktop.loadComponentFromURL("DOCUMENT", "_blank", 0, Array(Prop("Hidden", True), Prop("UpdateDocMode", 3)))
 indexes = doc.getDocumentIndexes()
 If indexes.getCount() = 0 Then
  finder = doc.createSearchDescriptor()
  finder.SearchString = "СОДЕРЖАНИЕ"
  found = doc.findFirst(finder)
  If Not IsNull(found) Then
   cursor = doc.Text.createTextCursorByRange(found.End)
   cursor.gotoNextParagraph(False)
   idx = doc.createInstance("com.sun.star.text.ContentIndex")
   idx.CreateFromOutline = True
   idx.Level = 2
   idx.Title = ""
   doc.Text.insertTextContent(cursor, idx, False)
  End If
 End If
 styles = doc.StyleFamilies.getByName("ParagraphStyles")
 For Each name In Array("Contents 1", "Contents 2", "TOC 1", "TOC 2")
  If styles.hasByName(name) Then
   st = styles.getByName(name)
   st.CharFontName = "Times New Roman"
   st.CharHeight = 12
   st.CharWeight = 100
   st.ParaFirstLineIndent = 0
   st.ParaLeftMargin = 0
   st.ParaTopMargin = 0
   st.ParaBottomMargin = 70
   Dim spacing As New com.sun.star.style.LineSpacing
   spacing.Mode = 0
   spacing.Height = 115
   st.ParaLineSpacing = spacing
  End If
 Next name
 indexes = doc.getDocumentIndexes()
 For i = 0 To indexes.getCount()-1
  indexes.getByIndex(i).update()
 Next i
 doc.getTextFields().refresh()
 doc.refresh()
 vc = doc.CurrentController.getViewCursor()
 vc.gotoEnd(False)
 For i = 0 To indexes.getCount()-1
  indexes.getByIndex(i).update()
 Next i
 doc.getTextFields().refresh()
 doc.store()
 doc.storeToURL("PDF", Array(Prop("FilterName", "writer_pdf_Export"), Prop("FilterData", Array(Prop("SelectPdfVersion", 1), Prop("ExportBookmarks", True)))))
 result = "["
 For i = 0 To doc.TextTables.getCount()-1
  table = doc.TextTables.getByIndex(i)
  If i > 0 Then result = result & ","
  result = result & "{""table"":" & (i+1) & ",""rows"":["
  For j = 0 To table.Rows.getCount()-1
   If j > 0 Then result = result & ","
   firstPage = 99999
   lastPage = 0
   For k = 0 To table.Columns.getCount()-1
    cell = table.getCellByPosition(k,j)
    vc.gotoRange(cell.Start, False)
    If vc.Page < firstPage Then firstPage = vc.Page
    vc.gotoRange(cell.End, False)
    If vc.Page > lastPage Then lastPage = vc.Page
   Next k
   result = result & "{""row"":" & (j+1) & ",""start"":" & firstPage & ",""end"":" & lastPage & "}"
  Next j
  result = result & "]}"
 Next i
 result = result & "]"
 f = FreeFile
 Open "MAPPING" For Output As #f
 Print #f, result
 Close #f
 f = FreeFile
 Open "RECEIPT" For Output As #f
 Print #f, "OK indexes=" & indexes.getCount()
 Close #f
 doc.close(True)
 StarDesktop.terminate()
 Exit Sub
Failed:
 f = FreeFile
 Open "RECEIPT" For Output As #f
 Print #f, "ERROR " & Err & ": " & Error$
 Close #f
 StarDesktop.terminate()
End Sub
'''
        for key, value in {'DOCUMENT': document.as_uri(), 'PDF': pdf.as_uri(),
                           'MAPPING': str(mapping), 'RECEIPT': str(receipt)}.items():
            source = source.replace('"'+key+'"', '"'+value.replace('"', '""')+'"')
        (standard/'Module1.xba').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">'''+html.escape(source)+'</script:module>', encoding='utf-8')
        subprocess.run([str(soffice), '--headless', '--nologo', '--nodefault', '--nofirststartwizard',
                        '-env:UserInstallation='+profile.as_uri(), 'macro:///Standard.Module1.Main()'],
                       check=True, timeout=90)
        message = receipt.read_text().strip() if receipt.exists() else 'No render receipt'
        if not message.startswith('OK'):
            raise RuntimeError(message)
        if table_map:
            Path(table_map).write_text(mapping.read_text(), encoding='utf-8')
        print(json.dumps({'pdf': str(pdf), 'fields': message}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--soffice', required=True)
    parser.add_argument('--document', required=True)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--table-map')
    args = parser.parse_args()
    render(args.soffice, args.document, args.pdf, args.table_map)
