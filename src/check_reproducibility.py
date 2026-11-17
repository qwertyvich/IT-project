"""Повторная генерация всех рисунков в изолированной папке внутри репозитория."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys,shutil,subprocess,hashlib,json,platform
from project_model import ROOT,SRC,FIG
from fonts import ARIAL,TIMES

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 node=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(shutil.which('node') or '')
 if not node.is_file():raise RuntimeError('Pass the Node.js executable as the first argument.')
 manifest=json.loads((SRC/'figures_manifest.json').read_text(encoding='utf-8'))
 filenames=[]
 for f in manifest:
  filenames.extend([f['name']+'.svg',f['name']+'.png'])
  if f['source']=='dot':filenames.append(f['name']+'.dot')
 expected={n:sha(FIG/n) for n in filenames}
 with TemporaryDirectory(prefix='.repro-',dir=ROOT) as tmp:
  target=Path(tmp).resolve()
  # The temporary tree and its eventual recursive cleanup must remain in this repo.
  assert target.is_relative_to(ROOT.resolve()) and target!=ROOT.resolve()
  source=target/'src';source.mkdir()
  for p in SRC.iterdir():
   if p.suffix in {'.py','.mjs'}:shutil.copy2(p,source/p.name)
  subprocess.run([sys.executable,str(source/'draw_figures.py')],cwd=target,check=True)
  subprocess.run([str(node),str(source/'render_figures.mjs'),str(target/'figures')],cwd=target,check=True)
  actual={n:sha(target/'figures'/n) for n in filenames}
  different=[n for n in filenames if expected[n]!=actual[n]]
  assert not different,different
 result={'diagrams':len(manifest),'generated_files_compared':len(filenames),'all_hashes_match':True,
         'python':platform.python_version(),'node':subprocess.check_output([str(node),'--version'],text=True).strip(),
         'arial_sha256':sha(ARIAL),'times_sha256':sha(TIMES),
         'scope':'Воспроизводимость графических артефактов на исходной машине; не испытания банковского ПО.'}
 (SRC/'reproducibility.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
