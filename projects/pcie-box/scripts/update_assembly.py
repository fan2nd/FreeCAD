from pathlib import Path
import FreeCAD as A
ROOT=Path(__file__).resolve().parents[1]
for d in list(A.listDocuments().values()):
 if (d.FileName and Path(d.FileName).parent==ROOT/'models') or (not d.FileName and d.Name.startswith('PCIeBox')):A.closeDocument(d.Name)
for name in ('build.py',):
 path=ROOT/'scripts'/name
 exec(compile(path.read_text(),str(path),'exec'),{'__file__':str(path)})
