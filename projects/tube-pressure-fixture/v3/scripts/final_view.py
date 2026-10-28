"""Run in FreeCAD GUI to save the final effective-component presentation."""
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui

def apply(doc):
    if not App.GuiUp:
        raise RuntimeError('Final presentation requires the FreeCAD GUI.')
    App.setActiveDocument(doc.Name)
    # Migrate existing files: ungroup members without deleting their history.
    for name in ('LowerHistory','UpperHistory'):
        group=doc.getObject(name)
        if group and group.TypeId=='App::DocumentObjectGroup':
            group.Group=[]
            doc.removeObject(name)
    for obj in doc.Objects:
        if obj.ViewObject:
            obj.ViewObject.Visibility = obj.Name in ('Lower', 'Upper', 'Plate')
    for name in ('Lower', 'Upper', 'Plate'):
        obj = doc.getObject(name)
        assert obj and obj.Shape.isValid() and len(obj.Shape.Solids) == 1
        obj.Label = {'Lower':'下座','Upper':'上盖','Plate':'形变板'}[name]
        obj.ViewObject.ShapeColor = tuple(obj.DisplayColor[:3])
        obj.ViewObject.DisplayMode = 'Flat Lines'
        obj.ViewObject.LineColor = (.16, .20, .24)
    Gui.Selection.clearSelection()
    # Finish deferred document initialization before setting the final camera.
    Gui.updateGui()
    view = Gui.activeDocument().activeView()
    view.setCameraOrientation((.4247082003, .1759198966, .3398511429, .8204732386))
    view.fitAll()
    Gui.updateGui()
    doc.recompute()
    doc.save()

if __name__ == '__main__':
    target = Path(__file__).resolve().parents[1] / 'models' / '管路压力工装.FCStd'
    doc = next((d for d in App.listDocuments().values()
                if d.FileName and Path(d.FileName).resolve() == target), None)
    if doc is None:
        doc = App.openDocument(str(target))
    apply(doc)
