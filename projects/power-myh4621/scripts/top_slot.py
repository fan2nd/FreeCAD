"""Update authorized top opening and compact base; preserve other features."""
from pathlib import Path
import shutil, math
import FreeCAD as A, MeshPart, Part
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'models/JD-Power_MYH-4621F-支架-完整装配.FCStd'
backup=ROOT.parents[1]/'.local/power-myh4621/下出线槽'
backup.mkdir(parents=True,exist_ok=True)
for source in [p,ROOT/'print/JD-Power_MYH-4621F-支架-立板.stl']:
    target=backup/source.name
    if not target.exists():shutil.copy2(source,target)
d=A.openDocument(str(p))
if d.getObject('WireMouthFillet'):
    d.Upright.Tip=d.WireMouthFillet.Base[0]
    d.removeObject('WireMouthFillet')
d.Base.Tip=d.JointPattern
for name in ['FixingPattern','FixingHole','FixingSketch']:
    if d.getObject(name):d.removeObject(name)
d.BaseOutline.setDatum(8,A.Units.Quantity('-32 mm'))
d.BaseOutline.setDatum(10,A.Units.Quantity('64 mm'))
d.recompute();before_base=d.Base.Shape.copy()
d.WireSketch.Placement.Rotation=A.Rotation(A.Vector(0,0,1),180)
d.WireSketch.Placement.Base.y=2
d.WireSketch.Label='上出线槽轮廓';d.WirePocket.Label='上出线槽'
d.recompute()
b=d.Upright
# Round only the two corners where the open slot meets the R23 outer arc.
previous=b.Tip
localshape=b.Shape.copy();localshape.Placement=b.Placement.inverse().multiply(localshape.Placement)
mouth=[]
for i,edge in enumerate(localshape.Edges,1):
    bb=edge.BoundBox
    if bb.XLength<1e-6 and bb.YLength<1e-6 and abs(abs(bb.XMin)-7)<1e-6 and abs(bb.YMin-math.sqrt(23**2-7**2))<1e-6 and bb.ZLength>5.99:
        mouth.append('Edge'+str(i))
assert len(mouth)==2,mouth
f=b.newObject('PartDesign::Fillet','WireMouthFillet');f.Label='缺口口角圆角'
f.Base=(previous,mouth);f.Radius=2;d.recompute();previous.Visibility=False
assert not f.Shape.isNull() and f.Shape.isValid() and len(f.Shape.Solids)==1
assert d.Upright.Shape.isValid() and len(d.Upright.Shape.Solids)==1
assert before_base.cut(d.Base.Shape).Volume<1e-8 and d.Base.Shape.cut(before_base).Volume<1e-8
local=d.Upright.Shape.copy();local.Placement=d.Upright.Placement.inverse().multiply(local.Placement)
assert local.isInside(A.Vector(0,-20,3),1e-6,True)
assert not local.isInside(A.Vector(0,20,3),1e-6,True)
for body in [d.Upright,d.Base]:
    for o in body.Group:o.Visibility=False
    body.Visibility=True;body.Tip.Visibility=True
d.save()
Part.export([d.Upright],str(ROOT/'models/立板.step'))
local.rotate(A.Vector(),A.Vector(1,0,0),180);local.translate(A.Vector(0,0,6))
MeshPart.meshFromShape(Shape=local,LinearDeflection=0.08,AngularDeflection=0.15,Relative=False).write(str(ROOT/'print/JD-Power_MYH-4621F-支架-立板.stl'))
Part.export([d.Base],str(ROOT/'models/底板.step'))
Part.export([d.Upright,d.Base],str(ROOT/'models/支架.step'))
assert abs(d.Base.Shape.BoundBox.XLength-64)<1e-8
MeshPart.meshFromShape(Shape=d.Base.Shape,LinearDeflection=0.08,AngularDeflection=0.15,Relative=False).write(str(ROOT/'print/JD-Power_MYH-4621F-支架-底板.stl'))
print('Original support updated: top slot 8 mm; base 64 x 55 x 6 with two joint holes.')
