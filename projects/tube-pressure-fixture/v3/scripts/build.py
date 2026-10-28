"""Three independent parts with editable native history. Geometric checks only."""
import sys,json,math,importlib.util
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part,MeshPart
V=A.Vector
ROOT=Path(__file__).resolve().parents[1]
for d in ('models','print','previews','reports'):(ROOT/d).mkdir(exist_ok=True)
P=dict(tube_od=3.9,tube_id=2.9,pressure_max_kpa=100.,length=42.5,width=36.6,
 base_height=6.,upper_height=4.4,plate_top=8.4,plate_width=8.9,plate_length=24.,
 plate_thickness=.6,end_thickness=2.2,notch_radius=1.95,notch_axis_z=5.85,
 window_half_y=9.,window_half_x=9.25,fit_gap=.3,wall_cover_gap=.4,wall_plate_gap=.4,wall_local_top=6.,
 gauge_length=8.8,gauge_width=7.5,grid_length=7.,grid_width=7.,gauge_center_y=-.55,
 layer_height=.2,nominal_preload=.15,upper_screw_web=2.,pilot_depth=4.8,
 pilot_diameter=2.8,clearance_diameter=3.3,screw_length=6.,motion_up=.6)
P['wall_relief_length']=P['plate_width']+2*P['wall_plate_gap']
P['wall_length']=2*(P['window_half_x']-P['wall_cover_gap'])
D=A.newDocument('TubeFixtureV3');D.Label='管路压力工装 v3'
spec=importlib.util.spec_from_file_location('fixture_history',ROOT/'scripts/history.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
b,u,p,blank=h.build_history(D,P)
parts=[(b,'下座',(.25,.5,.65)),(u,'上盖',(.77,.79,.83)),(p,'形变板',(.85,.61,.25))]
for o,label,color in parts:
 o.Label=label;o.addProperty('App::PropertyColor','DisplayColor');o.DisplayColor=color

def box(x,y,z,l,w,t):return Part.makeBox(l,w,t,V(x,y,z))
def cylinder(r):return Part.makeCylinder(r,60,V(-30,0,6),V(1,0,0))
pipe=cylinder(1.95).cut(cylinder(1.45))
def reference(name,label,shape):
 o=D.addObject('Part::Feature',name);o.Label=label;o.Shape=shape;return o
tube=reference('TubeReference','管道参考',pipe)
gauge=reference('GaugeReference','应变片参考',box(-3.75,-4.95,8.4,7.5,8.8,.15))
grid=reference('GridReference','敏感栅参考',box(-3.5,-3.5,8.55,7,7,.02))
sheet=D.addObject('Spreadsheet::Sheet','Parameters');sheet.Label='参数记录'
for col,value in [('A1','参数'),('B1','数值'),('C1','单位')]:sheet.set(col,value)
for row,(key,value) in enumerate(P.items(),2):
 sheet.set('A'+str(row),key);sheet.set('B'+str(row),str(value));sheet.set('C'+str(row),'kPa' if key=='pressure_max_kpa' else 'mm')
for col,width in [('A',210),('B',110),('C',80)]:sheet.setColumnWidth(col,width)
notes=D.addObject('Spreadsheet::Sheet','Notes');notes.Label='说明'
entries=[('参数表','记录表，不驱动几何；修改原生草图/拉伸/布尔特征，或脚本重建'),
 ('装配','下座、上盖、形变板三件独立打印；形变板先放入上盖底部限位槽，再与管道和下座装配'),
 ('限位','上盖两端各3mm压住形变板上表面；槽两侧及端面各0.3mm间隙，管道预压提供向上接触力；未粘接或固定形变板'),
 ('缺口','管轴X，圆弧R1.95，中心Y0 Z5.85；缺口顶部最薄0.6，端部2.2，板顶Z8.4'),
 ('采集','基底8.8×7.5；敏感栅总包络约7×7居中对准管道；焊点朝-Y端；基底偏置-0.55需按实物确认'),
 ('变形','中央圆弧上方截面最薄；厚度沿两侧增大。应变分布、峰值和桥路灵敏度未作FEA或实测验证'),
 ('打印','层高0.2；下座底面朝下，上盖顶面朝下，形变板贴片平面朝下。薄处0.6为3层，端部2.2为11层'),
 ('预压','名义0.15mm，由硅胶压缩及形变板弯曲共同吸收，非指定压紧力；曲面位置不按层高量化'),
 ('避让','中央9.7mm范围两侧壁均降到Z6；其余侧壁Z8.4；形变板端底Z6.2，距下座0.2'),
 ('限位间隙','下座限位段沿管轴各向中心移动0.2；外端到上盖窗口0.4，内端到形变板0.4；槽宽与预压不变'),
 ('边界','原管槽下半圆保持向下和横向几何约束；中央上半侧向约束由形变板缺口补充，打印误差和硅胶实际鼓胀需验证'),
 ('螺丝','M3×6普通螺丝；盖板孔3.3，过盖2、进入下座4；下座光孔2.8深4.8，咬合需试制'),
 ('活动','中心上挠0～0.6检查为规定弯曲形状的几何包络；端面保持贴顶。不是允许压力或材料行程结论')]
notes.set('A1','项目');notes.set('B1','说明')
for row,(key,value) in enumerate(entries,2):notes.set('A'+str(row),key);notes.set('B'+str(row),value)
notes.setColumnWidth('A',95);notes.setColumnWidth('B',750)
D.recompute()
checks={'parts':{},'intersections_mm3':{},'scope':'geometry only; no FEA or calibration'}
for o,_,_ in parts:
 assert o.Shape.isValid() and len(o.Shape.Solids)==1,o.Name
 checks['parts'][o.Name]={'volume_mm3':o.Shape.Volume,'valid':True,'solids':1}
for a,c in [(b,u),(b,p),(u,p)]:
 volume=a.Shape.common(c.Shape).Volume;assert volume<1e-7,(a.Name,c.Name,volume)
 checks['intersections_mm3'][a.Name+'_'+c.Name]=volume
assert b.Shape.common(pipe).Volume<1e-7
assert u.Shape.common(pipe).Volume<1e-7
assert p.Shape.common(pipe).Volume>0
assert abs(P['plate_top']-(P['notch_axis_z']+P['notch_radius'])-.6)<1e-8
assert abs(p.Shape.BoundBox.ZMin-6.2)<1e-8
assert p.Shape.distToShape(b.Shape)[0]>.19999
projection=box(-3.75,-4.95,8.3,7.5,8.8,.1)
assert abs(projection.common(p.Shape).Volume-projection.Volume)<1e-6
# Check final high wall segments, excluding the lower plate and screw posts.
checks['wall_gaps_mm']=[]
for sign in (-1,1):
    wall=b.Shape.common(box(0 if sign>0 else -10,-4.1,6.1,10,8.2,2.4))
    bb=wall.BoundBox
    inner=bb.XMin if sign>0 else -bb.XMax
    outer=bb.XMax if sign>0 else -bb.XMin
    plate_gap=inner-P['plate_width']/2
    cover_gap=P['window_half_x']-outer
    assert abs(plate_gap-.4)<1e-7 and abs(cover_gap-.4)<1e-7
    assert abs(wall.distToShape(u.Shape)[0]-.4)<1e-7
    assert abs(wall.distToShape(p.Shape)[0]-.4)<1e-7
    checks['wall_gaps_mm'].append({'side':sign,'to_cover':cover_gap,'to_plate':plate_gap})
checks['gauge_supported']=True
checks['preload_mm']=.15
checks['plate_base_gap_mm']=p.Shape.distToShape(b.Shape)[0]
# Real editable history: plate extrusion and sketch dimensions propagate to final cut.
original=blank.LengthFwd.Value;vol=p.Shape.Volume
blank.LengthFwd=original+.2;D.recompute();assert p.Shape.isValid() and p.Shape.Volume>vol
blank.LengthFwd=original;D.recompute();assert abs(p.Shape.Volume-vol)<1e-6
sk=blank.Base;ix=next(i for i in range(sk.ConstraintCount) if sk.Constraints[i].Name=='Width')
sk.setDatum(ix,A.Units.Quantity(P['plate_width']+.1));D.recompute();assert p.Shape.Volume>vol
sk.setDatum(ix,A.Units.Quantity(P['plate_width']));D.recompute();assert abs(p.Shape.Volume-vol)<1e-6
checks['history']={'sketch_edit_propagates':True,'extrusion_edit_propagates':True,'counts':{kind:sum(o.TypeId==kind for o in D.Objects) for kind in ('Sketcher::SketchObject','Part::Extrusion','Part::Cut','Part::MultiFuse')}}
# Continuous conservative vertical envelope for the clear center span.
# Ends at |Y|>=9 remain supported; central span may move upwards only.
envelope=box(-P['plate_width']/2,-8.99,6.2,P['plate_width'],17.98,2.2+P['motion_up'])
assert envelope.common(b.Shape).Volume<1e-7
assert envelope.common(u.Shape).Volume<1e-7
checks['center_upward_envelope_clear']=True
checks['end_bearing_length_mm']=3.
checks['slot_side_end_gap_mm']=.3
# Print on flat faces; round notch opens upward and requires no bridging.
for o,label,_ in parts:
 shape=o.Shape.copy()
 if o!=b:
  shape.rotate(V(),V(1,0,0),180);shape.translate(V(0,0,o.Shape.BoundBox.ZMax))
 assert abs(shape.BoundBox.ZMin)<1e-7
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.1,Relative=False)
 assert mesh.isSolid()
 mesh.write(str(ROOT/'print'/(label+'.stl')))
 previous=None;maximum=0.
 for i in range(round(shape.BoundBox.ZMax/.2)):
  z=.1+.2*i;sample=shape.common(box(-30,-30,z,60,60,.002));sample.translate(V(0,0,-z))
  if previous is not None:maximum=max(maximum,sample.cut(previous).Volume/.002)
  previous=sample
 assert maximum<1e-5,(label,maximum)
 checks['print_'+o.Name]={'closed_mesh':True,'unsupported_slice_area_mm2':maximum}
 Part.export([o],str(ROOT/'models'/(label+'.step')))
Part.export([b,u,p],str(ROOT/'models/管路压力工装.step'))
for o in D.Objects:
 if A.GuiUp:o.ViewObject.Visibility=o.Name in ('Lower','Upper','Plate')
D.recompute();D.saveAs(str(ROOT/'models/管路压力工装.FCStd'))
(ROOT/'reports/geometry.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
# Depth-buffer preview data for assembly, exploded assembly and transverse section.
colors={b.Name:'#598ca7',u.Name:'#bec8d6',p.Name:'#dda747'}
for mode in ['assembly','exploded','section']:
 data=[]
 for o,color in [(b,colors[b.Name]),(u,colors[u.Name]),(p,colors[p.Name]),(tube,'#60b6ae')]:
  shape=o.Shape
  if mode=='section':shape=shape.common(box(-.025,-25,-1,.05,50,20))
  offset=({'Upper':25,'Plate':12}.get(o.Name,0) if mode=='exploded' else 0)
  vv,tt=shape.tessellate(.06)
  for tri in tt:
   points=[]
   for i in tri:
    q=vv[i];x,y,z=q.x,q.y,q.z+offset
    points.append([530+24*y,545-24*z,x] if mode=='section' else [530+9*(.84*x-.54*y),540+9*(.30*x+.47*y-.83*z),.45*x+.7*y+.56*z])
   normal=(vv[tri[1]]-vv[tri[0]]).cross(vv[tri[2]]-vv[tri[0]])
   shade=.6+.4*abs(normal.z)/max(normal.Length,1e-12) if mode!='section' else 1
   shaded='#'+''.join('%02x'%int(int(color[j:j+2],16)*shade) for j in (1,3,5))
   data.append({'points':points,'color':shaded})
 (ROOT/'reports'/(mode+'.json')).write_text(json.dumps(data))
print(json.dumps(checks,ensure_ascii=False,indent=2))
if A.GuiUp:
 spec=importlib.util.spec_from_file_location('fixture_view',ROOT/'scripts/final_view.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.apply(D)
