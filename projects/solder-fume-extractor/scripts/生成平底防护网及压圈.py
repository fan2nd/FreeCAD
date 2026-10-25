from pathlib import Path
exec((Path(__file__).resolve().parent/'旋弧网格基础.py').read_text().split('gridvolume=')[0])
import tempfile,shutil
临时目录=tempfile.TemporaryDirectory(prefix='磁吸进气网-');OUT=Path(临时目录.name)
# Input order: from outlet at left, counterclockwise as viewed from intake face.
PIXELS=[(73,439),(106,497),(405,538),(430,513),(460,195),(432,170)]
RADII=[56.2,57,62.3,60.7,67.8,67.3]
HOLES=[]
for (x,y),distance in zip(PIXELS,RADII):
 dx=x-266;dy=360-y;L=math.hypot(dx,dy);HOLES.append((distance*dx/L,distance*dy/L))
def arm(x,y,width=10):
 L=math.hypot(x,y);ux=x/L;uy=y/L;nx=-uy*width/2;ny=ux*width/2
 ax=ux*42;ay=uy*42
 pts=[V(ax+nx,ay+ny,0),V(x+nx,y+ny,0),V(x-nx,y-ny,0),V(ax-nx,ay-ny,0)]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,2)).fuse(Part.makeCylinder(width/2,2,V(x,y,0)))
base=shape
for x,y in HOLES:base=base.fuse(arm(x,y))
cover=ring(44,40.3,2,0)
MAGNET_IDS=[0,1,4,5]
MAGNETS=[HOLES[i] for i in MAGNET_IDS]
for x,y in MAGNETS:
 tab=arm(x,y,9)
 cover=cover.fuse(tab)
 hole=Part.makeCylinder(2.55,4,V(x,y,-1))
 cover=cover.cut(hole)
for x,y in HOLES:
 base=base.cut(Part.makeCylinder(2.7,4,V(x,y,-1)))
 base=base.cut(Part.makeCone(3.6,2.7,.9,V(x,y,2),V(0,0,-1)))
base=base.removeSplitter();cover=cover.removeSplitter();cover.translate(V(0,0,2.2))
for s in [base,cover]:assert s.isValid() and len(s.Solids)==1 and abs(s.BoundBox.ZLength-2)<1e-6
assert base.common(cover).Volume<1e-6
for (x,y),expected in zip(HOLES,RADII):assert abs(math.hypot(x,y)-expected)<1e-7
for x,y in HOLES:
 assert base.common(Part.makeCylinder(2.69,2,V(x,y,0))).Volume<1e-6
 assert cover.common(Part.makeCone(2.7,3.6,.9,V(x,y,1.1))).Volume<1e-6
for x,y in MAGNETS:
 assert base.common(Part.makeCylinder(2.5,2,V(x,y,0))).Volume<1e-6
 assert cover.common(Part.makeCylinder(2.5,2,V(x,y,2.2))).Volume<1e-6
rootfile=(Path(__file__).resolve().parents[1]/'models/焊锡吸烟器.FCStd')
assembly=App.openDocument(str(rootfile))
camera_before=assembly.Bridge.Shape.exportBrepToString()
assembly.Grille.Shape=base;assembly.ClampRing.Shape=cover
assembly.Grille.Label='防护网 · 六孔沉头固定 · 厚2mm'
assembly.ClampRing.Label='磁吸滤布压圈 · 四处磁铁座（1/2/5/6） · 厚2mm'
for name in ['MagnetDiameter','MagnetThickness','MagnetPocketDiameter']:
 if name in assembly.Grille.PropertiesList:assembly.Grille.removeProperty(name)
for ob in [assembly.ClampRing]:
 for name,value in [('MagnetDiameter',5),('MagnetThickness',2),('MagnetPocketDiameter',5.1)]:
  if name not in ob.PropertiesList:ob.addProperty('App::PropertyLength',name,'Dimensions')
  setattr(ob,name,value)
p=assembly.EstimatedHoleCoordinates
p.Notes='从进风面看出风口朝左，起始左侧较高孔逆时针：56.2/57/62.3/60.7/67.8/67.3。径向距离实测，角度沿用图片估算。沉头7.2/90度，通孔5.4。压圈在1/2/5/6号螺丝头上方装直径5厚2磁铁，孔5.1贯通胶粘，直接吸铁质螺丝头；防护网无磁铁。'
for i,(x,y) in enumerate(HOLES):setattr(p,f'Hole{i+1}',V(x,y,0))
assembly.recompute()
assert assembly.GrilleBody.Shape.isValid() and assembly.ClampRingBody.Shape.isValid()
assert assembly.Bridge.Shape.exportBrepToString()==camera_before
for name,s in [('平底防护网',base),('滤布压圈',cover)]:
 s=s.copy();s.translate(V(0,0,-s.BoundBox.ZMin))
 mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.035,AngularDeflection=.15,Relative=False)
 assert mesh.isSolid();mesh.write(str(OUT/(name+'.stl')))
target=OUT/'整合工程.FCStd';assembly.saveAs(str(target));App.closeDocument(assembly.Name)
check=App.openDocument(str(target));check.recompute()
assert check.GrilleBody.Shape.isValid() and check.ClampRingBody.Shape.isValid()
shutil.copy2(target,rootfile)
finaldir=Path(__file__).resolve().parents[1]
(finaldir/'print').mkdir(parents=True,exist_ok=True)
for name in ['平底防护网','滤布压圈']:shutil.copy2(OUT/(name+'.stl'),finaldir/'print'/(name+'.stl'))
report={'radial_distances_mm':RADII,'hole_coordinates_mm':HOLES,'angle_source':'estimated_from_image','countersink_diameter_mm':7.2,'countersink_depth_mm':.9,'magnet_size_mm':[5,2],'magnet_hole_mm':5.1,'magnet_count':4,'magnet_target':'steel_screw_heads','magnet_at_holes':[1,2,5,6],'part_height_mm':2,'body_count':2,'assembly_interference_mm3':0,'physical_fit_verified':False}
f=finaldir/'reports/模型检查结果.json';f.parent.mkdir(parents=True,exist_ok=True);data=json.loads(f.read_text()) if f.exists() else {};data['平底进气网']=report;f.write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
