import sys,math,json
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part,MeshPart
V=App.Vector
import tempfile
临时目录=tempfile.TemporaryDirectory(prefix='相机桥生成-')
OUT=Path(临时目录.name)
P=1.27
R=3.175+0.15
r=(6.35-1.0825317547*P)/2+0.15
def bez(pts):
 b=Part.BezierCurve();b.setPoles([V(*p) for p in pts]);return b.toShape()
def line(a,b):return Part.makeLine(V(*a),V(*b))
edges=[bez([(-42,8,0),(-28,8,0),(-16,12,0),(0,12,0)]),bez([(0,12,0),(16,12,0),(28,8,0),(42,8,0)]),line((42,8,0),(52,8,0)),Part.Arc(V(52,8,0),V(60,0,0),V(52,-8,0)).toShape(),line((52,-8,0),(-52,-8,0)),Part.Arc(V(-52,-8,0),V(-60,0,0),V(-52,8,0)).toShape(),line((-52,8,0),(-42,8,0))]
plan=Part.Face(Part.Wire(edges)).extrude(V(0,0,-6))
sides=[line((-62,-20,0),(62,-20,0)),line((62,-20,0),(62,-20,-5)),line((62,-20,-5),(42,-20,-5)),bez([(42,-20,-5),(32,-20,-5),(22,-20,-6),(10,-20,-6)]),line((10,-20,-6),(-10,-20,-6)),bez([(-10,-20,-6),(-22,-20,-6),(-32,-20,-5),(-42,-20,-5)]),line((-42,-20,-5),(-62,-20,-5)),line((-62,-20,-5),(-62,-20,0))]
blank=plan.common(Part.Face(Part.Wire(sides)).extrude(V(0,40,0))).removeSplitter()
for x in [-52,52]:
 blank=blank.cut(Part.makeCylinder(2.7,7,V(x,0,-6))).cut(Part.makeCone(3.35,2.7,0.65,V(x,0,-5)))
def threaded(shape,z,h,offset=0):
 bore=Part.makeCylinder(r,h+2,V(0,offset,z-1))
 z0=0
 helix=Part.makeHelix(P,h+2*P,(R+r)/2)
 inner=r-0.12;half=P/16+(R-inner)/math.sqrt(3)
 pts=[V(inner,0,z0-half),V(R,0,z0-P/16),V(R,0,z0+P/16),V(inner,0,z0+half)]
 profile=Part.Wire(Part.makePolygon(pts+[pts[0]]).Edges)
 sections=[]
 turns=(h+2*P)/P
 count=math.ceil(turns*32)
 for i in range(count+1):
  angle=turns*360*i/count
  w=profile.copy();w.rotate(V(0,0,0),V(0,0,1),angle);w.translate(V(0,0,z-P+P*angle/360));sections.append(w)
 cutter=Part.makeLoft(sections,True,True)
 cutter.translate(V(0,offset,0))
 assert cutter.isValid()
 plain=shape.cut(bore)
 shape=plain.cut(cutter)
 print('extra thread removal',plain.Volume-shape.Volume,flush=True)
 assert plain.Volume-shape.Volume>5
 return shape.cut(Part.makeCone(R+0.25,r,0.8,V(0,offset,z))).removeSplitter()
shape=threaded(blank,-6,6,2)
assert shape.isValid() and len(shape.Solids)==1
doc=App.newDocument('SmoothCameraBridge');doc.Label='104mm相机固定桥 · 紧凑版 · 打印螺纹'
ob=doc.addObject('PartDesign::Feature','Bridge');ob.Label='连续曲面连接桥 · 1/4-20右旋内螺纹';ob.Shape=shape
params=doc.addObject('App::FeaturePython','Dimensions')
for name,val in [('MountHoleSpacing',104),('EndThickness',5),('HeadRecessDepth',0),('FanEarThickness',5),('EffectiveClampThickness',5),('ScrewLength',10),('NominalFanPenetration',5),('CenterThickness',6),('CenterWidth',20),('EndWidth',16),('ThreadOffsetY',2),('ScrewHeadDiameter',6.5),('CountersinkDiameter',6.7),('CountersinkDepth',0.65),('ThreadPitch',P),('ThreadNominalDiameter',6.35),('PrintRadialAllowance',0.15)]:
 params.addProperty('App::PropertyLength',name,'Dimensions');setattr(params,name,val)
params.addProperty('App::PropertyString','Notes');params.Notes='相机孔为实际打印螺旋几何，无金属螺母。两端为自攻螺丝沉头让位孔，头径6.5、总长10，直接拧入5厚风扇，无螺母。参数为记录，修改生成脚本重建。'
doc.recompute();doc.saveAs(str(OUT/'相机固定桥.FCStd'))
Part.export([ob],str(OUT/'相机固定桥.step'))
mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=0.025,AngularDeflection=0.12,Relative=False)
mesh.write(str(OUT/'相机固定桥.stl'))
coupon=threaded(Part.makeCylinder(8,6,V(0,0,-6)),-6,6)
assert coupon.isValid() and len(coupon.Solids)==1
MeshPart.meshFromShape(Shape=coupon,LinearDeflection=0.025,AngularDeflection=0.12,Relative=False).write(str(OUT/'相机螺纹试拧件.stl'))
for x in [-52,52]:assert shape.common(Part.makeCylinder(2.5,5,V(x,0,-3))).Volume<1e-6
assert shape.common(Part.makeCylinder(r-0.01,16,V(0,2,-15))).Volume<1e-6
report={'valid':shape.isValid(),'solids':len(shape.Solids),'pitch_mm':P,'radial_clearance_mm':0.15,'mesh_closed':mesh.isSolid(),'mesh_facets':mesh.CountFacets,'hole_spacing_mm':104,'end_round_diameter_mm':16,'thread_offset_y_mm':2,'straight_side_y_mm':-8,'end_thickness_mm':5,'head_recess_mm':0,'fan_ear_mm':5,'screw_length_mm':10,'nominal_fan_penetration_mm':5,'physical_fit_verified':False}
assert mesh.isSolid()
(OUT/'检查结果.json').write_text(json.dumps(report,indent=2))
App.closeDocument(doc.Name);doc=App.openDocument(str(OUT/'相机固定桥.FCStd'));assert doc.Bridge.Shape.isValid()
print(json.dumps(report,indent=2))

import shutil
rootfile=(Path(__file__).resolve().parents[1]/'models/焊锡吸烟器.FCStd')
assembly=App.openDocument(str(rootfile))
oldvolume=assembly.Bridge.Shape.Volume
oldplacement=assembly.CameraMount.Placement
backup=OUT/'整合工程-孔距104前.FCStd'
if not backup.exists():shutil.copy2(rootfile,backup)
assembly.Bridge.Shape=shape.copy()
assembly.Bridge.Label='同边双孔连接桥 · 1/4-20右旋打印螺纹'
assembly.Dimensions.CenterThickness=6
assembly.Dimensions.MountHoleSpacing=104
for name,value in [('CenterWidth',20),('EndWidth',16),('ThreadOffsetY',2)]:
 if name not in assembly.Dimensions.PropertiesList:assembly.Dimensions.addProperty('App::PropertyLength',name,'Dimensions')
 setattr(assembly.Dimensions,name,value)
assembly.recompute()
assert assembly.CameraMount.Placement==oldplacement
assert assembly.Bridge.Shape.isValid()
tempfile=OUT/'更新后整合工程.FCStd'
assembly.saveAs(str(tempfile))
App.closeDocument(assembly.Name)
verify=App.openDocument(str(tempfile))
assert len([o for o in verify.Objects if o.TypeId=='PartDesign::Feature'])==3
assert verify.Bridge.Shape.isValid()
shutil.copy2(tempfile,rootfile)
# Export bridge in the existing flipped pose, centered on the build plate.
posed=shape.copy();posed.Placement=oldplacement.multiply(posed.Placement)
posed.translate(V(-posed.BoundBox.Center.x,-posed.BoundBox.Center.y,-posed.BoundBox.ZMin))
MeshPart.meshFromShape(Shape=posed,LinearDeflection=.025,AngularDeflection=.12,Relative=False).write(str(OUT/'相机固定桥-边孔版.stl'))
print(json.dumps({'old_volume':oldvolume,'new_volume':shape.Volume,'volume_reduction_percent':100*(1-shape.Volume/oldvolume),'overall_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength],'integrated_project_updated':True},indent=2))

finaldir=Path(__file__).resolve().parents[1]
(finaldir/'print').mkdir(parents=True,exist_ok=True)
shutil.copy2(OUT/'相机固定桥-边孔版.stl',finaldir/'print/相机固定桥-孔距104-厚6.stl')
shutil.copy2(OUT/'相机螺纹试拧件.stl',finaldir/'print/相机螺纹试拧件.stl')
checks=finaldir/'reports/模型检查结果.json'
checks.parent.mkdir(parents=True,exist_ok=True);data=json.loads(checks.read_text()) if checks.exists() else {};data['相机固定桥']=report;checks.write_text(json.dumps(data,ensure_ascii=False,indent=2))
# Straight side spans between the two end-circle tangent points.
assert shape.BoundBox.YMin > -8.00001
assert abs(shape.BoundBox.YMax-12)<0.001
print('最新整合工程和中文名打印文件已更新；两端圆直径16，相机孔横向偏移2。')
