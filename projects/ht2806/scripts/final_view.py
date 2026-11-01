from pathlib import Path
import FreeCAD as A, FreeCADGui as G
from PySide import QtCore, QtWidgets
ROOT=Path(__file__).resolve().parents[1]
d=A.ActiveDocument
def settle():
    G.updateGui()
    loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(400,loop.quit);loop.exec_()
for o in d.Motor.Group:o.Visibility=False
d.Motor.Visibility=True;d.Motor.Tip.Visibility=True
G.Selection.clearSelection()
v=G.activeDocument().activeView()
for widget in G.getMainWindow().findChildren(QtWidgets.QDockWidget):
    if widget.objectName() in ('Tasks','Python console'):widget.hide()
settle()
v.viewAxonometric();v.fitAll();settle()
v.saveImage(str(ROOT/'previews/前侧.png'),1400,1100,'White')
v.setCameraOrientation(A.Rotation(A.Vector(1,0,0),145).Q);v.fitAll();settle()
v.saveImage(str(ROOT/'previews/后侧.png'),1400,1100,'White')
v.viewAxonometric();v.fitAll();settle()
d.recompute();d.save()
