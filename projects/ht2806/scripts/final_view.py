from pathlib import Path
import FreeCAD as A, FreeCADGui as G
from PySide import QtCore, QtWidgets
ROOT=Path(__file__).resolve().parents[1]
d=A.ActiveDocument
v=G.activeDocument().activeView()
def settle():
    G.updateGui();loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(450,loop.quit);loop.exec_()
def shot(name):
    settle();v.fitAll();settle();v.saveImage(str(ROOT/'previews'/name),1400,1100,'White')
G.activateWorkbench('PartWorkbench');G.Selection.clearSelection()
for body in [d.Motor,d.Upright,d.Base,d.Board,d.MotorScrew1,d.MotorScrew2]:
    for o in body.Group:o.Visibility=False
    body.Tip.Visibility=True;body.Visibility=True
    color=(.25,.28,.32) if body==d.Motor else ((.12,.52,.23) if body==d.Board else (.72,.76,.81))
    body.ViewObject.ShapeColor=color;body.Tip.ViewObject.ShapeColor=color
d.MotorScrew1.Visibility=False;d.MotorScrew2.Visibility=False;d.Board.Visibility=False;d.Upright.Visibility=False;d.Base.Visibility=False
v.viewAxonometric();shot('前侧.png')
v.setCameraOrientation(A.Rotation(A.Vector(1,0,0),145).Q);shot('后侧.png')
d.MotorScrew1.Visibility=False;d.MotorScrew2.Visibility=False;d.Motor.Visibility=False;d.Upright.Visibility=True;d.Base.Visibility=True
v.setCameraOrientation(A.Rotation(A.Vector(-1,1,0),A.Vector(0,0,1),A.Vector(1,1,.8),'ZXY').Q);shot('支架.png')
d.Base.Visibility=False;shot('立板.png')
d.Base.Visibility=True;d.Motor.Visibility=True;d.MotorScrew1.Visibility=True;d.MotorScrew2.Visibility=True;shot('装配.png');d.recompute();d.save()
# PCB envelope remains hidden in the delivered assembly.
d.Board.Visibility=False
G.Selection.clearSelection();v.fitAll();settle();d.recompute();d.save()
