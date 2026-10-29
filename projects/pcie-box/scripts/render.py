from pathlib import Path
import FreeCAD as A, FreeCADGui as G
from PySide import QtCore
ROOT=Path(__file__).resolve().parents[1]
doc=A.ActiveDocument
view=G.activeDocument().activeView()
def settle():
 loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(400,loop.quit);loop.exec_();G.updateGui()
G.Selection.clearSelection()
doc.Lid.Visibility=False
view.viewTop();view.fitAll();settle()
view.saveImage(str(ROOT/'previews'/'contour.png'),1400,900,'White')
view.viewAxonometric();view.fitAll();settle()
view.saveImage(str(ROOT/'previews'/'interior.png'),1400,900,'White')
doc.Lid.Visibility=True
view.fitAll();settle()
view.saveImage(str(ROOT/'previews'/'assembly.png'),1400,900,'White')
doc.recompute();doc.save()
