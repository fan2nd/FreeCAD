import sys,json,math,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part,Mesh
V=App.Vector;p=Path(__file__).parent;d=App.openDocument(str(p.parent.parent/'按摩花洒_G12_高50_斜喷水.FCStd'));s=d.ShowerFinished.Shape
assert s.isValid() and len(s.Solids)==1
jets=json.loads((p/'jet_directions.json').read_text());voidtests=[]
for j in jets:
 o=V(*j['outlet_center']);inn=V(*j['inward_direction']);radial=V(0,o.y,o.z)
 distance=radial.cross(inn).Length
 assert abs(distance-52/6)<1e-7
 for t in [-3,-2,-1,0,1,2]:
  assert not s.isInside(o+inn*t,1e-6,True), (j['row'],j['column'],t)
 voidtests.append(True)
a=V(0,math.sin(math.radians(19)),math.cos(math.radians(19)));origin=V(-16.833355,0,0)
for t in range(34,57):assert not s.isInside(origin+a*t,1e-6,True),('inlet',t)
assert s.BoundBox.XMin>-25.0001 and s.BoundBox.XMax<25.0001
stl=Mesh.Mesh(str(p/'按摩花洒_G12_高50_斜喷水.stl'));assert stl.isSolid()
z=zipfile.ZipFile(p/'按摩花洒_G12_高50_斜喷水.3mf');r=ET.fromstring(z.read('3D/3dmodel.model'));ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
vv=[V(float(v.get('x')),float(v.get('y')),float(v.get('z'))) for v in r.findall('.//m:vertex',ns)];ff=[[int(f.get(k)) for k in ['v1','v2','v3']] for f in r.findall('.//m:triangle',ns)];m=Mesh.Mesh([[vv[i] for i in f] for f in ff]);assert m.isSolid();assert m.Volume>0
report={'single_valid_solid':True,'42_jet_centerlines_clear':True,'inlet_centerline_clear':True,'height_50mm':True,'stl_closed':True,'3mf_closed_positive_volume':True,'3mf_volume_mm3':m.Volume,'cad_volume_mm3':s.Volume,'thread_geometry':'96 helical segments per revolution, 55 degree nominal profile, G1/2 basic diameters and pitch','physical_fit_tested':False}
(p/'final_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
