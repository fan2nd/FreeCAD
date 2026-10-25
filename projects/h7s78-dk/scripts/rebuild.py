import sys, json, shutil, os, math
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A, Part, MeshPart
V=A.Vector
FLOOR=1.6
CLEARANCE=10.0
TOP=FLOOR+CLEARANCE
SHIFT=TOP-12.4
BASE=Path(__file__).resolve().parents[1]
MODELS=BASE/'models'; PRINT=BASE/'print'; PREVIEWS=BASE/'previews'; REPORTS=BASE/'reports'
for directory in (MODELS,PRINT,PREVIEWS,REPORTS): directory.mkdir(parents=True,exist_ok=True)
source=MODELS/'h7s78-dk.FCStd'; backup=MODELS/'h7s78-dk-original.FCStd'
if not backup.exists(): shutil.copy2(source,backup)
d=A.openDocument(str(backup)); body=d.getObject('Body'); old=body.Shape.copy()
# Original construction is retained as editable history. These final stages replace its supports.
shell=d.Pocket.Shape.copy()
shell.translate(V(0,0,SHIFT))
shell=shell.common(Part.makeBox(160,106,20,V(-5,-5,0)))
shell=shell.cut(Part.makeBox(150.4,96.4,3+SHIFT-FLOOR,V(-.2,-.2,FLOOR)))
for before,after in [('MultiTransform','Pocket001'),('Pocket001','Pocket002'),('Pocket002','Pocket003'),('Pocket003','Pocket004')]:
    opening=d.getObject(before).Shape.cut(d.getObject(after).Shape)
    opening.translate(V(0,0,SHIFT))
    shell=shell.cut(opening)
def rounded(x,y,w,h,r,z=3,height=9.4):
    s=Part.makeBox(w,h,height,V(x,y,z))
    edges=[e for e in s.Edges if e.BoundBox.ZLength>height-.001]
    return s.makeFillet(r,edges)
def feature(name,label,s):
    o=body.newObject('PartDesign::Feature',name);o.Label=label;o.Shape=s
    return o
def bez(points):
    curve=Part.BezierCurve();curve.setPoles([V(x,y,FLOOR) for x,y in points]);return curve.toShape()
def line(a,b):return Part.makeLine(V(*a,FLOOR),V(*b,FLOOR))
def solid(edges):return Part.Face(Part.Wire(edges)).extrude(V(0,0,CLEARANCE))
# Each support shares a broad full-height footprint with the wall. Cubic curves
# have matching tangents at both the wall and the inner bearing surface.
corner=solid([line((-.4,-.4),(-.4,15)),line((-.4,15),(-.2,15)),
    bez([(-.2,15),(-.2,10.2),(10.2,10.2),(10.2,5)]),
    bez([(10.2,5),(10.2,-.2),(12,-.2),(15,-.2)]),
    line((15,-.2),(15,-.4)),line((15,-.4),(-.4,-.4))])
s=shell
for sx,sy in [(1,1),(-1,1),(1,-1),(-1,-1)]:
    mat=A.Matrix();mat.A11=sx;mat.A22=sy;mat.A14=150 if sx<0 else 0;mat.A24=96 if sy<0 else 0
    s=s.fuse(corner.transformGeometry(mat))
for x,w,depth,top in [(25,10,10,True),(75,50,5,True),(35,65,3,False)]:
    baseline=96.2 if top else -.2; sign=-1 if top else 1
    def p(u,v):return (u,baseline+sign*v)
    reach=4
    a=p(x-reach,0);b=p(x+3,depth);c=p(x+w-3,depth);e=p(x+w+reach,0)
    edges=[bez([a,p(x,0),p(x,depth),b]),line(b,c),bez([c,p(x+w,depth),p(x+w,0),e]),
           line(e,p(x+w+reach,-.2)),line(p(x+w+reach,-.2),p(x-reach,-.2)),line(p(x-reach,-.2),a)]
    s=s.fuse(solid(edges))
s=s.removeSplitter()
rounded_stage=feature('RoundedSupports','支撑与边框一体化 · 相切曲线过渡',s)
# Smooth the floor junction, within the original support envelopes wherever possible.
floor_edges=[e for e in s.Edges if abs(e.BoundBox.ZMin-3)<1e-6 and abs(e.BoundBox.ZMax-3)<1e-6]
try:
    trial=s.makeFillet(.8,floor_edges)
    if trial.isValid() and len(trial.Solids)==1: s=trial
except Exception: pass
rootstage=feature('RootRounds','圆弧支撑基体',s)
hole_sk=body.newObject('Sketcher::SketchObject','M3PilotSketch');hole_sk.Label='M3自攻底孔 Ø2.6 · 四孔140×86'
hole_sk.Placement.Base=V(0,0,TOP)
import Sketcher
for x,y in [(5,5),(145,5),(5,91),(145,91)]:
    i=hole_sk.addGeometry(Part.Circle(V(x,y,0),V(0,0,1),1.3),False)
    hole_sk.addConstraint(Sketcher.Constraint('Diameter',i,2.6))
    hole_sk.addConstraint(Sketcher.Constraint('DistanceX',i,3,x))
    hole_sk.addConstraint(Sketcher.Constraint('DistanceY',i,3,y))
hole_sk.addProperty('App::PropertyString','Instructions');hole_sk.Instructions='默认Ø2.6用于M3塑料自攻打样；按螺丝牙型、材料和实测打印孔径微调。'
d.recompute()
body.Tip=rootstage
holes=body.newObject('PartDesign::Pocket','M3PilotPocket');holes.Label='M3自攻盲孔 · 深10mm · 到底板上表面';holes.Profile=hole_sk;holes.Length=CLEARANCE
d.recompute();s=holes.Shape
assert not s.isNull() and s.isValid() and len(s.Solids)==1
assert abs(s.BoundBox.XLength-old.BoundBox.XLength)<1e-6
assert abs(s.BoundBox.YLength-old.BoundBox.YLength)<1e-6
for x,y in [(5,5),(145,5),(5,91),(145,91)]:
    assert s.common(Part.makeCylinder(1.299,CLEARANCE-.001,V(x,y,FLOOR+.001))).Volume<1e-6
    assert s.common(Part.makeCylinder(1.3,FLOOR-.001,V(x,y,0))).Volume>8.48
# No new solid material is allowed in the upper PCB seating plane.
assert s.common(Part.makeBox(150,96,1.5,V(0,0,TOP+.1))).Volume<1e-6
before_honey=s.copy()
keepout=s.common(Part.makeBox(160,106,.1,V(-5,-5,FLOOR+.01)))
hs=body.newObject('Sketcher::SketchObject','HoneycombSketch');hs.Label='蜂窝密铺 · 旋转30° · 对边10.3mm · 筋宽1.6mm';hs.Placement.Base=V(0,0,FLOOR)
radius=10.3/math.sqrt(3); pitch=11.9; count=0;min_clearance=100
cells=[]
angle=math.radians(30)
for col in range(-12,13):
    u=col*pitch*math.sqrt(3)/2
    for row in range(-12,13):
        v=row*pitch+(col%2)*pitch/2
        x=75+u*math.cos(angle)-v*math.sin(angle)
        y=48+u*math.sin(angle)+v*math.cos(angle)
        pts=[V(x+radius*math.cos(i*math.pi/3+angle),y+radius*math.sin(i*math.pi/3+angle),0) for i in range(6)]
        if min(p.x for p in pts)<.8 or max(p.x for p in pts)>149.2 or min(p.y for p in pts)<.8 or max(p.y for p in pts)>95.2:continue
        prism=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,3.2))
        clearance=prism.distToShape(keepout)[0]
        if clearance<1.6-1e-7:continue
        min_clearance=min(min_clearance,clearance)
        for i in range(6):hs.addGeometry(Part.LineSegment(pts[i],pts[(i+1)%6]),False)
        cells.append((x,y,prism))
        count+=1
actual_gaps=[a[2].distToShape(b[2])[0] for i,a in enumerate(cells) for b in cells[i+1:] if math.hypot(a[0]-b[0],a[1]-b[1])<pitch+.001]
assert actual_gaps and all(abs(g-1.6)<1e-6 for g in actual_gaps)
assert all(abs(c[2].BoundBox.XLength-10.3)<1e-6 for c in cells)
d.recompute();body.Tip=holes
hp=body.newObject('PartDesign::Pocket','HoneycombPocket');hp.Label='蜂窝贯穿1.6mm底板 · %d孔'%count;hp.Profile=hs;hp.Length=FLOOR
d.recompute();s=hp.Shape
assert s.isValid() and len(s.Solids)==1
upper=Part.makeBox(160,106,13,V(-5,-5,FLOOR+.001))
assert before_honey.common(upper).cut(s).Volume<1e-6
assert min_clearance>=1.6-1e-7
# Lower only the top rim 20–86 mm from the PCB right edge (X=150).
before_relief=s.copy()
relief_sk=body.newObject('Sketcher::SketchObject','ExtensionClearanceSketch')
relief_sk.Label='顶部拓展板避让 · 距PCB右边20–86mm'
relief_sk.Placement.Base=V(0,0,14+SHIFT)
rp=[V(64,96,0),V(130,96,0),V(130,99,0),V(64,99,0)]
for i in range(4):relief_sk.addGeometry(Part.LineSegment(rp[i],rp[(i+1)%4]),False)
d.recompute();body.Tip=hp
relief=body.newObject('PartDesign::Pocket','ExtensionClearancePocket')
relief.Label='顶部X64–130边框降至螺柱顶面 Z11.6'
relief.Profile=relief_sk;relief.Length=14+SHIFT-TOP
d.recompute();hp=relief;s=hp.Shape
assert s.isValid() and len(s.Solids)==1
relief_region=Part.makeBox(66,3,5,V(64,96,TOP))
assert s.common(relief_region).Volume<1e-6
assert before_relief.cut(s).cut(relief_region).Volume<1e-6
assert abs(s.common(Part.makeBox(10,2,15,V(90,96.2,0))).BoundBox.ZMax-TOP)<1e-6
for o in d.Objects:
    if hasattr(o,'Visibility'):o.Visibility=False
body.Visibility=True;hp.Visibility=True;body.Tip=hp
d.recompute();d.Label='H7S78-DK 底盖 · 圆润内腔 · M3自攻'
d.saveAs(str(source))
mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.06,AngularDeflection=.15,Relative=False)
mesh.write(str(PRINT/'h7s78-dk-Body.stl'))
Part.export([hp],str(MODELS/'h7s78-dk-rounded-M3.step'))
report={'valid':s.isValid(),'solids':len(s.Solids),'mesh_closed':mesh.isSolid(),'outer_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength], 'hole_pitch_mm':[140,86],'pilot_diameter_mm':2.6,'pilot_depth_mm':CLEARANCE,'hole_floor_z_mm':FLOOR,'support_top_z_mm':TOP,'root_fillet_applied':abs(rootstage.Shape.Volume-rounded_stage.Shape.Volume)>1e-5}
assert abs(before_honey.common(Part.makeBox(1,1,4,V(70,45,0))).BoundBox.ZMax-FLOOR)<1e-6
assert len(s.common(Part.makeBox(160,106,.1,V(-5,-5,2))).Solids)==1
report.update(floor_thickness_mm=FLOOR,pcb_clearance_mm=CLEARANCE,support_wall_transition='tangent cubic curves, full height',honeycomb_rotation_deg=30,honeycomb_cells=count,honeycomb_across_flats_mm=10.3,measured_neighbor_gap_mm=min(actual_gaps),honeycomb_web_mm=1.6,minimum_keepout_mm=min_clearance,upper_features_unchanged=True)
report.update(extension_rim_top_z_mm=TOP,extension_relief_xy_mm=[64,96,130,99],extension_removed_volume_mm3=before_relief.Volume-s.Volume)
(REPORTS/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
# Render actual tessellated geometry, not a conceptual illustration.
os.environ['MPLCONFIGDIR']='/private/tmp/h7s78_mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig=plt.figure(figsize=(13,8),facecolor='#f6f7f9')
ax=fig.add_subplot(111,projection='3d',facecolor='#f6f7f9')
v,f=mesh.Topology;v=np.array([[p.x,p.y,p.z] for p in v]);faces=v[np.array(f)]
colors=['#456f7a' if t[:,2].mean()>10 else '#81b5be' if t[:,2].mean()>1.4 else '#bdced2' for t in faces]
ax.add_collection3d(Poly3DCollection(faces,facecolors=colors,linewidths=0,antialiased=False))
ax.set(xlim=(-5,155),ylim=(-5,101),zlim=(0,24));ax.set_box_aspect((160,106,24));ax.view_init(elev=90,azim=-90);ax.set_proj_type('ortho');ax.set_axis_off()
fig.tight_layout();fig.savefig(PREVIEWS/'preview.png',dpi=160)
