from pathlib import Path
import json
import FreeCAD as A, FreeCADGui as Gui
from PySide import QtCore,QtWidgets
ROOT=Path(__file__).resolve().parents[1]
doc=A.ActiveDocument
base=doc.getObject('Base');lid=doc.getObject('Lid');card=doc.getObject('Card');cover=doc.getObject('Cover')
r=json.loads((ROOT/'reports'/'assembly_check.json').read_text())
checks=doc.addObject('App::DocumentObjectGroup','FitChecks');checks.Label='干涉检查'
for i,item in enumerate(r['collisions'],1):
 b=next(b for b in card.Group if b.Label==item['card_part'])
 c=doc.addObject('Part::Common','Collision'+str(i));c.Label='干涉'+str(i);c.Base=b;c.Tool=base if item['case_part']=='下盒' else lid;checks.addObject(c)
 doc.recompute();c.ViewObject.ShapeColor=(1.0,0.1,0.05);c.Visibility=False
checks.Visibility=False
r['touching_parts']=[p['name'] for p in r['parts'] if any(c['intersection_mm3']<1e-6 and c['distance_mm']<1e-6 for c in p['checks'].values())]
r['gold_slot_clearance_x_mm']=(-78+93*168/165)-16
(ROOT/'reports'/'assembly_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
notes=doc.getObject('FitNotes');notes.set('A7','金手指槽');notes.set('B7','槽右端已加宽，沿X净余量约0.691 mm；其余轮廓保持。');notes.set('A8','贴壁');notes.set('B8','左上挡片上端与PCB顶边齐平；左侧补两处SFP外伸包络；端部贴壁处已增加避空。')
Gui.Selection.clearSelection();view=Gui.activeDocument().activeView()
def settle():
 loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(500,loop.quit);loop.exec_();Gui.updateGui()
base.Visibility=True;lid.Visibility=False;card.Visibility=True
for b in card.Group:
 b.Visibility=True
 for o in b.Group:o.Visibility=False
 b.Tip.Visibility=True
cover.Visibility=False
view.viewTop();view.fitAll();settle();view.saveImage(str(ROOT/'previews'/'装配轮廓.png'),1600,1000,'White')
cover.Visibility=True;lid.Visibility=True;checks.Visibility=False
for o in checks.Group:o.Visibility=False
for b in (base,lid):
 b.Visibility=True
 for o in b.Group:o.Visibility=False
 b.Tip.Visibility=True
Gui.activateWorkbench('PartWorkbench')
for w in Gui.getMainWindow().findChildren(QtWidgets.QDockWidget):
 if w.objectName() in ('Python console','Tasks'):w.hide()
view.viewAxonometric();view.fitAll();settle();doc.recompute();doc.save()
