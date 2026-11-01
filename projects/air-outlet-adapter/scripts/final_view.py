"""Finalize the active GUI document after its MDI view has been created."""
from pathlib import Path
import FreeCAD as A
import FreeCADGui as G
from PySide import QtCore

root=Path(__file__).resolve().parents[1]
doc=A.ActiveDocument
assert doc and doc.getObject('Adapter'), 'Open the air outlet adapter document first'
A.setActiveDocument(doc.Name)
G.Selection.clearSelection()
view=G.activeDocument().activeView()
view.viewAxonometric()
view.fitAll()

def capture():
    view.saveImage(str(root/'previews/转接头.png'),1200,1000,'Current')
    doc.save()

# Allow the new camera to be painted before the offscreen export.
QtCore.QTimer.singleShot(1000,capture)
