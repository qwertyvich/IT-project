"""Архив воспроизводимых исходников; готовые документы публикуются отдельно."""
from pathlib import Path
import hashlib,json,zipfile
from project_model import ROOT,SRC,OUT

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 paths=[ROOT/n for n in ['README.md','AGENTS.md','CONTEXT.md','requirements.txt','package.json']]
 paths += [p for p in SRC.iterdir() if p.is_file() and p.name!='package_summary.json']
 paths += [p for folder in ['figures','docs','contracts'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
 payload={p.relative_to(ROOT).as_posix():p.read_bytes() for p in sorted(paths)}
 payload['ARCHIVE_INFO.md']=('Исходники проекта банковской информационной системы.\n\n'
  'PDF и DOCX опубликованы отдельно в папке «Готовая работа» репозитория:\n'
  'https://github.com/qwertyvich/IT-project\n\n'
  'Порядок сборки: README.md. Контекст продолжения: CONTEXT.md.\n'
  'Полные тексты стандартов, чужая записка и исходные сообщения сюда не включены.\n').encode('utf-8')
 manifest={name:sha(data) for name,data in payload.items()}
 payload['archive_manifest.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
 target=OUT/'Исходники проекта.zip'
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name,data in sorted(payload.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,11,24,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
   info.external_attr=0o644<<16;z.writestr(info,data)
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  assert set(z.namelist())==set(payload)
  for name,data in payload.items():assert z.read(name)==data,name
 result={'file':target.relative_to(ROOT).as_posix(),'entries':len(payload),'bytes':target.stat().st_size,'sha256':sha(target.read_bytes()),'verified':True}
 (SRC/'package_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
