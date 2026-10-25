import sys, math, json, time
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App, Part, MeshPart
V=App.Vector
BASE=Path(__file__).resolve().parents[1]
MODELS=BASE/'models'; PRINT=BASE/'print'; PREVIEWS=BASE/'previews'; REPORTS=BASE/'reports'
for directory in (MODELS,PRINT,PREVIEWS,REPORTS): directory.mkdir(parents=True,exist_ok=True)
D=App.newDocument('ShowerG12H30');D.Label='按摩花洒 · G1-2 · 高30 · 斜喷水'
checks={}
def check(name,s):
 info={'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume}
 print(name,info,flush=True);checks[name]=info
 assert info['valid'] and info['solids']==1,name
 return s
def feature(name,label,s):
 o=D.addObject('PartDesign::Feature',name);o.Label=label;o.Shape=s
 return o
def revolved(poly):
 pp=[V(x,r,0) for x,r in poly];pp.append(pp[0]);return Part.Face(Part.makePolygon(pp)).revolve(V(),V(1,0,0),360)
# Original ring envelopes rebuilt as smooth CAD surfaces; length reduced to 30.
outer=revolved([(-15,29),(-12,26),(12,26),(15,29),(15,37),(12,40),(-14,40),(-15,39)])
check('outer',outer)
a=25-2;h=1.82842712474619
cavity=revolved([(-13,29.82842712474619),(-13+h,28),(13-h,28),(13,29.82842712474619),(13,36.1715728752538),(13-h,38),(-13,38)])
shell=check('water_chamber',outer.cut(cavity).removeSplitter())
body=feature('RingChamber','01 环形水腔 · Ø80 / Ø52 / 厚30',shell)
# Six circumferential positions, four axial rows; water rays are tangent
# to a concentric circle of diameter 52/3, giving asin(1/3)=19.4712 degrees.
R=26.;impact=R/3;alpha=math.asin(impact/R)
cutters=[];jets=[]
for row in range(4):
 x=-7.5+row*5
 for col in range(6):
  theta=math.radians(-18+col*60+(row%2)*30)
  er=V(0,math.cos(theta),math.sin(theta));et=V(0,-math.sin(theta),math.cos(theta))
  outward=er*math.cos(alpha)+et*math.sin(alpha)
  p=V(x,0,0)+er*R
  cutters.append(Part.makeCylinder(.75,8,p-outward*2,outward))
  jets.append({'row':row+1,'column':col+1,'outlet_center':list(p),'inward_direction':list(-outward),'tangent_circle_radius':impact})
holed=check('angled_24_jets',shell.cut(Part.makeCompound(cutters)).removeSplitter())
jetob=feature('AngledJets','02 斜喷水孔 · 24×Ø1.5 · 切线圆Ø17.33',holed)
# G1/2 rounded profile sampled on a helical surface, then sewn as a solid.
# Build the retained flat directly instead of cutting a spline afterwards.
import Mesh
pitch=25.4/14;major=20.655;depth=.640327*pitch;minor=major-2*depth
rmax=major/2;rmin=minor/2;rho=.137329*pitch;end=56.5
axis=V(0,math.sin(math.radians(19)),math.cos(math.radians(19)))
rot=App.Rotation(V(0,0,1),axis)
tanpoint=rho*math.cos(math.radians(27.5));rootpoint=pitch/2-tanpoint
rtip=rmax-rho+rho*math.sin(math.radians(27.5))
def basic_tooth(z,theta):
 phase=(z-41.3-theta*pitch/(2*math.pi)+pitch/2)%pitch-pitch/2
 zz=abs(phase)
 if zz<=tanpoint:return rmax-rho+math.sqrt(max(0,rho*rho-zz*zz))
 if zz<rootpoint:return rtip-(zz-tanpoint)/math.tan(math.radians(27.5))
 return rmin+rho-math.sqrt(max(0,rho*rho-(pitch/2-zz)**2))
# Keep crest diameter and pitch; relieve flanks and deepen root smoothly.
def tooth(z,theta):
 phase=(z-41.3-theta*pitch/(2*math.pi)+pitch/2)%pitch-pitch/2
 u=abs(phase)/(pitch/2)
 shifted=abs(phase)+.10*math.sin(math.pi*u)
 base_z=41.3+theta*pitch/(2*math.pi)+shifted
 return basic_tooth(base_z,theta)-.25*u*u
def radius(z,theta):
 if z<=41:return 11.5-(z-38)*(11.5-rmax)/3
 rr=tooth(z,theta)
 if z<41.15:rr=rmax+(rr-rmax)*(z-41)/.15
 return min(rr,rmax+max(0,end-.8-z) if z<end-.8 else rmax-(z-(end-.8)))
N=96;vertices=[];columns=[];bottom=[];top=[]
for i in range(N):
 theta=i*2*math.pi/N
 zz={38.,41.,41.15,end-.8,end}
 for turn in range(-2,12):
  for offset in sorted(set([-pitch/2,-rootpoint,-tanpoint,-tanpoint/2,0,tanpoint/2,tanpoint,rootpoint,pitch/2]+[pitch*(k/24-.5) for k in range(25)])):
   z=41.3+theta*pitch/(2*math.pi)+turn*pitch+offset
   if 41.15<z<end:zz.add(z)
 col=[]
 for z in sorted(zz):
  rr=radius(z,theta)
  if math.cos(theta)<0:rr=min(rr,-8.166645/math.cos(theta))
  col.append((z,len(vertices)));vertices.append(V(rr*math.cos(theta),rr*math.sin(theta),z))
 columns.append(col)
 bottom.append(len(vertices));vertices.append(V(6*math.cos(theta),6*math.sin(theta),38))
 top.append(len(vertices));vertices.append(V(6*math.cos(theta),6*math.sin(theta),end))
faces=[]
for i in range(N):
 j=(i+1)%N;aa=columns[i];bb=columns[j];ia=ib=0
 while ia<len(aa)-1 or ib<len(bb)-1:
  if ib==len(bb)-1 or (ia<len(aa)-1 and aa[ia+1][0]<=bb[ib+1][0]):
   faces.append((aa[ia][1],bb[ib][1],aa[ia+1][1]));ia+=1
  else:
   faces.append((aa[ia][1],bb[ib][1],bb[ib+1][1]));ib+=1
 ai=aa[0][1];bi=bb[0][1];at=aa[-1][1];bt=bb[-1][1]
 faces.extend([(ai,bottom[i],bottom[j]),(ai,bottom[j],bi),(at,bt,top[j]),(at,top[j],top[i]),(bottom[i],top[i],top[j]),(bottom[i],top[j],bottom[j])])
cm=Mesh.Mesh([[vertices[k] for k in f] for f in faces]);print('explicit thread mesh',cm.CountFacets,cm.isSolid(),cm.Volume,flush=True)
if cm.Volume<0:cm.flipNormals()
assert cm.isSolid()
facets=Part.Shape();facets.makeShapeFromMesh(cm.Topology,.000001)
connector=Part.makeSolid(facets)
check('thread_connector_flat_local',connector)
connector.Placement=App.Placement(V(-6.833355,0,0),rot)
check('thread_connector_flat',connector)
threadob=feature('G12Connector','03 G1/2 外螺纹 · 保留切平面',connector)
final=holed.fuse(connector).removeSplitter()
# Open the inlet through the outer wall into the annular chamber only.
port=Part.makeCylinder(6,end-34+1,V(-6.833355,0,0)+axis*34,axis)
final=check('final',final.cut(port).removeSplitter())
obj=feature('ShowerFinished','成品 · 高30 · G1/2 · 斜喷水',final)
for name,val in [('BodyLength',30.),('InnerDiameter',52.),('OuterDiameter',80.),('JetDiameter',1.5),('JetTangentCircleDiameter',52/3),('ThreadPitch',pitch),('ThreadMajorDiameter',major),('ThreadMinorBasicDiameter',minor),('ThreadMinorRelievedDiameter',minor-.5),('ThreadRootRadialRelief',.25),('ThreadFlankPhaseRelief',.10),('InletBoreDiameter',12.)]:
 obj.addProperty('App::PropertyLength',name,'尺寸记录（非参数化）');setattr(obj,name,val)
obj.addProperty('App::PropertyInteger','JetCount','尺寸记录（非参数化）');obj.JetCount=24
obj.addProperty('App::PropertyAngle','JetAngleFromRadial','尺寸记录（非参数化）');obj.JetAngleFromRadial=math.degrees(alpha)
obj.addProperty('App::PropertyString','Notes','说明');obj.Notes='实体几何重建，非参数化；修改尺寸记录不会改变几何。原孔口圆角简化为直通圆孔Ø1.5；24孔分4排，相邻排圆周错开30度；各孔沿同一周向偏转，射线切线圆直径为内径的1/3。螺纹按G1/2公称直径、螺距和55°圆弧牙形重建，螺旋按每圈96段重建为缝合实体，主体保持光滑CAD曲面；主体为光滑CAD曲面。配合修订：外径由20.955mm缩至20.655mm，保持螺距，牙底径向加深0.25mm，牙侧中段约每侧削薄0.10mm，向牙顶平滑过渡；打印配合待试装。'
D.recompute()
for ob in [body,jetob,threadob]:ob.Visibility=False
obj.Visibility=True
D.saveAs(str(MODELS/'按摩花洒_G12_高30_斜喷水_螺纹缩径_交错孔版.FCStd'))
Part.export([obj],str(MODELS/'按摩花洒_G12_高30_斜喷水_螺纹缩径_交错孔版.step'))
print('Meshing final solid...',flush=True)
mesh=MeshPart.meshFromShape(Shape=final,LinearDeflection=.025,AngularDeflection=.12,Relative=False)
assert mesh.isSolid(), 'mesh not closed'
mesh.write(str(PRINT/'按摩花洒_G12_高30_斜喷水_螺纹缩径_交错孔版.stl'))
# One-object 3MF, mm units, oriented on the retained flat end face for printing.
import zipfile,xml.etree.ElementTree as ET
vv,ff=mesh.Topology
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
root=ET.Element('{'+ns+'}model',unit='millimeter');res=ET.SubElement(root,'resources');ob=ET.SubElement(res,'object',id='1',type='model');mm=ET.SubElement(ob,'mesh');vertices=ET.SubElement(mm,'vertices');triangles=ET.SubElement(mm,'triangles')
# Canonical x -> build z, canonical z -> build x. Right-handed proper rotation.
for p in vv:ET.SubElement(vertices,'vertex',x=f'{p.z:.7f}',y=f'{p.y:.7f}',z=f'{p.x+15:.7f}')
# Transform swaps X/Z, so reverse triangle winding to preserve outward normals.
for a,b,c in ff:ET.SubElement(triangles,'triangle',v1=str(a),v2=str(c),v3=str(b))
build=ET.SubElement(root,'build');ET.SubElement(build,'item',objectid='1')
with zipfile.ZipFile(PRINT/'按摩花洒_G12_高30_斜喷水_螺纹缩径_交错孔版.3mf','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
 z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
 z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
# Reopen the saved engineering file, so validation covers persistence too.
App.closeDocument(D.Name);loaded=App.openDocument(str(MODELS/'按摩花洒_G12_高30_斜喷水_螺纹缩径_交错孔版.FCStd'));assert loaded.ShowerFinished.Shape.isValid()
checks['summary']={'closed_mesh':mesh.isSolid(),'triangles':mesh.CountFacets,'jet_count':24,'jet_angle_degrees':math.degrees(alpha),'tangent_circle_diameter':52/3,'body_length':30,'flat_plane_x':-15,'thread_pitch':pitch,'thread_major_diameter':major,'thread_minor_basic_diameter':minor,'thread_minor_diameter':minor-.5,'root_radial_relief':.25,'flank_phase_relief':.10,'physical_fit_tested':False,'original_mouth_fillets_simplified':True}
(REPORTS/'validation.json').write_text(json.dumps(checks,indent=2));(REPORTS/'jet_directions.json').write_text(json.dumps(jets,indent=2))
print(json.dumps(checks['summary'],indent=2),flush=True)
