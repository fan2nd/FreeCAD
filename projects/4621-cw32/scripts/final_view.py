from pathlib import Path
import FreeCAD as A, FreeCADGui as G
from PySide import QtCore, QtWidgets
ROOT=Path(__file__).resolve().parents[1]
d=A.ActiveDocument
v=G.activeDocument().activeView()
def settle():
    G.updateGui();loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(350,loop.quit);loop.exec_()
def shot(name):
    settle();v.setCameraOrientation(A.Rotation(A.Vector(-1,1,0),A.Vector(0,0,1),A.Vector(1,1,0.8),'ZXY').Q);v.fitAll();settle();v.saveImage(str(ROOT/'previews'/name),1400,1100,'White')
G.Selection.clearSelection()
G.activateWorkbench('PartWorkbench')
for body in [d.Upright,d.Base,d.Board]:
    for o in body.Group:o.Visibility=False
    body.Visibility=True;body.Tip.Visibility=True
for body,color in [(d.Upright,(0.72,0.76,0.81)),(d.Base,(0.72,0.76,0.81)),(d.Board,(0.12,0.52,0.23))]:
    body.ViewObject.ShapeColor=color;body.Tip.ViewObject.ShapeColor=color
v.setCameraOrientation(A.Rotation(A.Vector(-1,1,0),A.Vector(0,0,1),A.Vector(1,1,0.8),'ZXY').Q)
d.Board.Visibility=False
shot('装配.png')
d.Board.Visibility=True
d.Board.ViewObject.Transparency=55;d.Board.Tip.ViewObject.Transparency=55
shot('板位示意.png')
d.Board.Visibility=False;d.Base.Visibility=False
shot('立板.png')
d.Upright.Visibility=True;d.Base.Visibility=True
G.Selection.clearSelection();v.fitAll();d.recompute();d.save()
# Collapse history trees while keeping all native dependencies.
for tree in G.getMainWindow().findChildren(QtWidgets.QTreeWidget):
    if tree.objectName()=='':continue
    tree.collapseAll()
    if tree.topLevelItemCount():tree.expandItem(tree.topLevelItem(0))
settle()
