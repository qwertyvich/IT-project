"""Поиск используемых гарнитур на исходном Windows-компьютере и на Mac."""
from pathlib import Path
import os
def locate(env,candidates):
 values=([os.environ[env]] if os.environ.get(env) else [])+candidates
 for value in values:
  p=Path(value).expanduser()
  if p.is_file():return p
 raise FileNotFoundError(f'Font not found. Install Arial/Times New Roman or set {env} to the font file.')
ARIAL=locate('BANK_FONT_ARIAL',[
 'C:/Windows/Fonts/arial.ttf','/System/Library/Fonts/Supplemental/Arial.ttf',
 '/Library/Fonts/Arial.ttf','~/Library/Fonts/Arial.ttf'])
TIMES=locate('BANK_FONT_TIMES',[
 'C:/Windows/Fonts/times.ttf','/System/Library/Fonts/Supplemental/Times New Roman.ttf',
 '/Library/Fonts/Times New Roman.ttf','~/Library/Fonts/Times New Roman.ttf'])
