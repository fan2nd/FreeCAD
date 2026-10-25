import sys,math,json,os
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A,Part,MeshPart
V=A.Vector;BASE=Path(__file__).resolve().parents[1]
MODELS=BASE/'models'; PRINT=BASE/'print'; PREVIEWS=BASE/'previews'; REPORTS=BASE/'reports'
for directory in (MODELS,PRINT,PREVIEWS,REPORTS): directory.mkdir(parents=True,exist_ok=True)
d=A.newDocument('ScreenStandV2');d.Label='V2 · 主板背装 · 一体短底座'
place=A.Placement(V(0,0,4-5*math.sin(math.radians(15))),A.Rotation(V(1,0,0),75))
def box(x,y,z,l,w,h):return Part.makeBox(l,w,h,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def tr(s):
 t=s.copy();t.Placement=place.multiply(t.Placement);return t
def obj(n,label,s,c):
 o=d.addObject('PartDesign::Feature',n);o.Label=label;o.Shape=s;o.addProperty('App::PropertyColor','PreviewColor');o.PreviewColor=c
 if A.GuiUp:o.ViewObject.ShapeColor=c
 return o
screen_holes=[(-24.5,45.5),(24.5,45.5),(-25.5,103.5),(24.5,103.5)]
board_holes=[(x,y) for x in [-22.55,22.55] for y in [33.45,80.55]]
frame=box(-36.4,0,-3,72.8,112,3)
frame=frame.makeFillet(4,[e for e in frame.Edges if e.BoundBox.ZLength>2.9 and e.CenterOfMass.y>111])
opening=box(-17.5,14,-12,34,100,16)
opening=opening.makeFillet(4,[e for e in opening.Edges if e.BoundBox.ZLength>15.9 and e.CenterOfMass.y<15])
frame=frame.cut(opening)
frame=frame.makeFillet(.6,[e for e in frame.Edges if e.BoundBox.ZLength<.01])
for x,y in screen_holes:frame=frame.cut(cyl(x,y,-4,1.4,5))
for x,y in board_holes:
 frame=frame.fuse(cyl(x,y,-8,3,5.5))
 frame=frame.cut(cyl(x,y,-9,1.05,7))
# Base connection: 3mm shoulder in base + 3mm engagement into the frame.

frame=frame.removeSplitter()
# Separate short foot retains the screen's lower-edge contact on Z=4.
foot=box(-36.4,-14,0,72.8,52,4)
foot=foot.makeFillet(6,[e for e in foot.Edges if e.BoundBox.ZLength>3.9 and e.BoundBox.XLength<.01 and e.BoundBox.YLength<.01])
foot=foot.makeFillet(.7,[e for e in foot.Edges if e.BoundBox.ZLength<.01])
foot=foot.removeSplitter()
combined=tr(frame).fuse(foot).removeSplitter()
# Straight ribs with vertical rear edges, without rib fillets.
for x in [-36.4,32.4]:
 # Y=18 leaves clearance to the closest estimated USB plug envelope.
 rib_top_local_y=(18-2*math.cos(math.radians(15)))/math.sin(math.radians(15))
 low=place.multVec(V(x,1,-2));high=place.multVec(V(x,rib_top_local_y,-2))
 tip=V(x,high.y,3)
 rib=Part.Face(Part.makePolygon([low,high,tip,low])).extrude(V(4,0,0))
 combined=combined.fuse(rib)
# Remove every projection in front of the screen mounting plane.
rear_half=tr(box(-100,-100,-200,200,300,200))
combined=combined.common(rear_half).removeSplitter()
foot=foot.common(rear_half).removeSplitter()
frame_obj=obj('OnePieceStand','V2一体支架 · 主板背装 · 短底座',combined,(.26,.58,.65))
screen=box(-36.4,0,5,72.8,129,5.6)
for x,y in screen_holes:screen=screen.fuse(cyl(x,y,0,2.7,5).cut(cyl(x,y,0,1.25,4)))
screen_obj=obj('Screen','屏幕参考 · FPC在上',tr(screen),(.14,.15,.17))
pcb=box(-25,31,-9.6,50,52,1.6)
for x,y in board_holes:pcb=pcb.cut(cyl(x,y,-10,1.4,3))
pcb_obj=obj('PCB','主板背装 · 元件朝后 · 柱高5外径6',tr(pcb),(.12,.29,.20))
lcd=obj('LCD','LCD座示意 · 向上出线',tr(box(0,70,-12.6,23,4,3)),(.82,.81,.72))
port=obj('ScreenFPC','屏幕上部FPC示意',tr(box(-11,95,1,22,7,3)),(.82,.81,.72))
net=box(-27,60,-23.6,21,17,14)
usb=box(-28,52,-24.6,20,7,15)
power=box(21,52.5,-13.6,7,9,4)
ios=[obj('Ethernet','网口估算包络',tr(net),(.65,.68,.7)),obj('USBData','USB数据口估算包络',tr(usb),(.65,.68,.7)),obj('USBPower','供电USB估算包络',tr(power),(.65,.68,.7))]
plugs=[box(-65,57,-32,38,23,24),box(-65,49,-32,37,14,25),box(28,49,-22,37,16,15)]
screws=[]
for x,y in screen_holes:screws.append(tr(cyl(x,y,-3,1.25,6).fuse(cyl(x,y,-4.8,2.25,1.8))))
for x,y in board_holes:screws.append(tr(cyl(x,y,-9.6,1.25,6).fuse(cyl(x,y,-11.4,2.25,1.8))))

hardware=obj('Screws','参考螺丝 · 屏幕4+主板4',Part.makeCompound(screws),(.65,.67,.70))
for s in [frame,foot,combined]:assert s.isValid() and len(s.Solids)==1

assert combined.common(tr(pcb)).Volume<1e-6
# The central lower screen-mounting web remains 3mm thick (no rear ledge).
assert combined.common(tr(box(-28,5,-8,56,8,4.99))).Volume<1e-6
assert foot.common(tr(screen)).Volume<1e-6
assert combined.common(tr(screen)).Volume<1e-6
for s in [net,usb,power]+plugs:
 assert combined.common(tr(s)).Volume<1e-6
# Check every PCB screw from the rear, including a 6mm driver shaft.
for x,y in screen_holes:
 assert combined.common(tr(cyl(x,y,-4.8,2.25,1.8))).Volume<1e-6
 assert combined.common(tr(cyl(x,y,-143,3,139.99))).Volume<1e-6
for x,y in board_holes:
 tool=tr(cyl(x,y,-149.6,3,140))
 for fixed in [combined,tr(screen),tr(net),tr(usb),tr(power),lcd.Shape]:assert fixed.common(tool).Volume<1e-6
# Orient the whole one-piece stand with the screen-facing side down.
print_shape=combined.copy();print_shape.Placement=place.inverse().multiply(print_shape.Placement)
print_shape.rotate(V(),V(0,1,0),180)
temp=MeshPart.meshFromShape(Shape=print_shape,LinearDeflection=.03,AngularDeflection=.1,Relative=False)
zmin=min(p.z for p in temp.Topology[0]);print_shape.translate(V(0,0,-zmin))
assert abs(zmin)<1e-5,'Screen-facing plane must sit on the print bed'
m=MeshPart.meshFromShape(Shape=print_shape,LinearDeflection=.06,AngularDeflection=.15,Relative=False)
assert m.isSolid();m.write(str(PRINT/'V2一体支架_屏幕侧朝下.stl'))
Part.export([frame_obj],str(MODELS/'V2一体支架_主板背装.step'))
sheet=d.addObject('Spreadsheet::Sheet','Dimensions')
rows=[('屏幕','竖屏后倾15度；中间四孔；FPC朝上；四孔固定，无前沿承托'),('底座','宽72.8；原52深坯料裁去前沿，后端Y=38；厚4'),('主板','平行屏幕背装，元件朝后；LCD向上'),('PCB支柱','高5、外径6、底孔2.1深6'),('螺丝','屏幕4颗M2.5×6，主板4颗M2.5×6自攻'),('结构','一体式，不分件，不增加连接螺丝'),('打印','屏幕安装面直接贴床，全部材料在平面后方'),('装配','先装屏幕，再从背面固定主板'),('说明','接口为估算包络；稳定性未实测')]
rows.extend([('屏幕固定片','上下统一厚3mm，取消下部凸台'),('加强筋','两侧各厚4mm，后缘Y=18竖直，直边无圆角；上端收短避让USB')])
for i,(k,v) in enumerate(rows,1):sheet.set('A'+str(i),k);sheet.set('B'+str(i),v)
sheet.setColumnWidth('A',180);sheet.setColumnWidth('B',420)
d.recompute();d.saveAs(str(MODELS/'V2主板背装_短底座.FCStd'))
report={'valid':combined.isValid(),'solids':len(combined.Solids),'parts':1,'base_width':72.8,'base_rear_y':38,'base_blank_depth_before_front_trim':52,'front_trimmed_to_screen_mount_plane':True,'pcb_standoff_height':5,'pcb_standoff_diameter':6,'pcb_rear_driver_clearance_diameter':6,'pcb_rear_driver_clearance_length':140,'screen_supported_by':'four screws, no front lip','extra_base_screws':0,'printing':'screen-facing mounting plane directly on bed; one piece','mounting_plane_height_above_print_bed':-zmin,'connector_dimensions':'photo estimate','stability':'not validated; PCB mass moved higher'}
report.update({'screen_web_thickness':3,'lower_ledge':False,'rib_profile':'straight vertical rear edge, no fillets','rib_count':2,'rib_thickness':4,'rib_foot_rear_y':high.y})
(REPORTS/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
os.environ['MPLCONFIGDIR']='/private/tmp/screen_stand_mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import LightSource
fig=plt.figure(figsize=(14,8),facecolor='#f4f6f8')
for j in [1,2]:
 ax=fig.add_subplot(1,2,j,projection='3d');ax.set_facecolor('#f4f6f8');allf=[];allc=[]
 for o in [frame_obj,screen_obj,pcb_obj,lcd,port,hardware]+ios:
  m=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.15,AngularDeflection=.2,Relative=False);vs,fs=m.Topology
  verts=np.array([[p.x,p.y,p.z] for p in vs]);pending=list(verts[np.array(fs)]);faces=[]
  while pending:
   a,b,c=pending.pop()
   if max(np.linalg.norm(a-b),np.linalg.norm(b-c),np.linalg.norm(c-a))>10:
    ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2;pending.extend([[a,ab,ca],[ab,b,bc],[ca,bc,c],[ab,bc,ca]])
   else:faces.append([a,b,c])
  allf.extend(faces);allc.extend([tuple(o.PreviewColor[:3])]*len(faces))
 ax.add_collection3d(Poly3DCollection(allf,facecolors=allc,linewidths=0,antialiased=False,shade=True,lightsource=LightSource(azdeg=300,altdeg=50)))
 ax.set(xlim=(-42,42),ylim=(-18,60),zlim=(0,140));ax.set_box_aspect((84,78,140));ax.set_proj_type('ortho');ax.view_init(elev=22 if j==1 else 0,azim=120 if j==1 else 0);ax.set_axis_off();ax.set_title('V2 / REAR-MOUNTED PCB' if j==1 else 'SIDE / SHORT BASE')
fig.subplots_adjust(0,0,1,.95,0,0);fig.savefig(PREVIEWS/'preview.png',dpi=160)
print(json.dumps(report,ensure_ascii=False))
