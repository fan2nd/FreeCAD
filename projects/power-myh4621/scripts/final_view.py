from pathlib import Path
import FreeCAD as A, FreeCADGui as G
from PySide import QtCore
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'previews').mkdir(exist_ok=True)
d=A.ActiveDocument
for body in [d.Upright,d.Base]:
    for o in body.Group:o.Visibility=False
    body.Visibility=True;body.Tip.Visibility=True
G.Selection.clearSelection()
v=G.activeDocument().activeView()
loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(350,loop.quit);loop.exec_()
v.setCameraOrientation(A.Rotation(A.Vector(-1,1,0),A.Vector(0,0,1),A.Vector(1,1,.8),'ZXY').Q)
v.fitAll();G.updateGui()
loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(500,loop.quit);loop.exec_()
v.fitAll();G.updateGui()
v.saveImage(str(ROOT/'previews/装配.png'),1400,1100,'White');d.save()
