import sys,math,json
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part,MeshPart
V=App.Vector
import tempfile
基础临时目录=tempfile.TemporaryDirectory(prefix='旋弧网格-')
OUT=Path(基础临时目录.name)
THICK=2.0
WEB=1.2
def cyl(r,h=THICK,z=0):return Part.makeCylinder(r,h,V(0,0,z))
def ring(ro,ri,h=THICK,z=0):return cyl(ro,h,z).cut(cyl(ri,h,z))
def point(r,k):
 a=2*math.pi*k/16+math.radians(28)*(r/40.7)**1.3
 return (r*math.cos(a),r*math.sin(a))
pieces=[ring(44,40.3),cyl(4)]
for r in [14,26,37]:pieces.append(ring(r+WEB/2,r-WEB/2))
paths=[]
for k in range(16):
 pts=[point(3.5+(40.9-3.5)*i/40,k) for i in range(41)]
 # Offset a sampled smooth spiral into a closed constant-width ribbon.
 left=[];right=[]
 for i,(x,y) in enumerate(pts):
  a=pts[max(0,i-1)];b=pts[min(len(pts)-1,i+1)]
  dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
  nx=-dy/length*WEB/2;ny=dx/length*WEB/2
  left.append(V(x+nx,y+ny,0));right.append(V(x-nx,y-ny,0))
 poly=left+list(reversed(right));poly.append(poly[0])
 pieces.append(Part.Face(Part.makePolygon(poly)).extrude(V(0,0,THICK)))
 paths.append(pts)
shape=pieces[0].multiFuse(pieces[1:]).removeSplitter()
gridvolume=shape.Volume
lip=ring(41.1,39.7,1.2,THICK)
shape=shape.fuse(lip).removeSplitter()
assert shape.isValid() and len(shape.Solids)==1
doc=App.newDocument('InletGrille');doc.Label='Ø82.5进气口 · 旋弧圆网 · 短定位环'
ob=doc.addObject('PartDesign::Feature','Grille');ob.Label='一体打印格网＋定位凸缘';ob.Shape=shape
p=doc.addObject('App::FeaturePython','Dimensions')
for name,value in [('InletMeasuredDiameter',82.5),('OuterDiameter',88),('GridThickness',1.6),('RibWidth',1.2),('LocatingLipOuterDiameter',82.2),('LocatingLipInnerDiameter',79.4),('LocatingLipHeight',1.2)]:
 p.addProperty('App::PropertyLength',name,'Dimensions');setattr(p,name,value)
p.addProperty('App::PropertyString','Notes');p.Notes='82.5为用户实测；定位环外径82.2，直径间隙0.3，非保证过盈卡扣。插入深1.2需核对叶轮净空；参数仅记录，修改脚本重建。'
doc.recompute();doc.saveAs(str(OUT/'基础进气网.FCStd'))
Part.export([ob],str(OUT/'基础进气网.step'))
mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=0.035,AngularDeflection=0.15,Relative=False)
assert mesh.isSolid();mesh.write(str(OUT/'基础进气网.stl'))
report={'valid':shape.isValid(),'solids':len(shape.Solids),'mesh_closed':mesh.isSolid(),'overall_height_mm':shape.BoundBox.ZLength,'lip_outer_diameter_mm':82.2,'diametral_clearance_mm':0.3,'physical_fit_verified':False}
(OUT/'检查结果.json').write_text(json.dumps(report,indent=2))
# Front-view drawing uses exactly the model's rib centerlines.
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-49 -49 98 98"><rect x="-49" y="-49" width="98" height="98" fill="#f3f5f7"/>','<g fill="none" stroke="#254759">','<circle r="42.15" stroke-width="3.7"/>']
for rr in [14,26,37]:svg.append(f'<circle r="{rr}" stroke-width="1.2"/>')
for pts in paths:svg.append('<polyline points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in pts)+'" stroke-width="1.2"/>')
svg+=['</g><circle r="4" fill="#254759"/></svg>']
(OUT/'进气网预览.svg').write_text(''.join(svg))
App.closeDocument(doc.Name);doc=App.openDocument(str(OUT/'基础进气网.FCStd'));assert doc.Grille.Shape.isValid()
print(json.dumps(report,indent=2))
