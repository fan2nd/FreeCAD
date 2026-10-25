import sys, math, json, os
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A, Part, MeshPart
V=A.Vector
BASE=Path(__file__).resolve().parents[1]
MODELS=BASE/'models'; PRINT=BASE/'print'; PREVIEWS=BASE/'previews'; REPORTS=BASE/'reports'
for directory in (MODELS,PRINT,PREVIEWS,REPORTS): directory.mkdir(parents=True,exist_ok=True)
d=A.newDocument('PortraitScreenStand')
d.Label='L型支架 · 双加强筋 · 中间四螺丝 · 后倾15°'
rot=A.Rotation(V(1,0,0),75)
screen_origin_z=4-5*math.sin(math.radians(15))
place=A.Placement(V(0,0,screen_origin_z),rot)
def tr(s):
 s=s.copy();s.Placement=place.multiply(s.Placement);return s
def box(x,y,z,l,w,h):return Part.makeBox(l,w,h,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def obj(name,label,shape,color):
 o=d.addObject('PartDesign::Feature',name);o.Label=label;o.Shape=shape
 o.addProperty('App::PropertyColor','PreviewColor');o.PreviewColor=color
 if A.GuiUp:o.ViewObject.ShapeColor=color
 return o
p=d.addObject('Spreadsheet::Sheet','Dimensions');p.Label='尺寸记录（修改后需同步建模脚本）'
rows=[('屏幕旋转 / 主板旋转','均旋转180度；屏幕FPC在上方'),('屏幕宽/高','72.8 / 129 mm'),('后倾','15 deg'),('固定孔','中间四孔：竖向58，两排横向50/49，图片读数'),('屏幕下边缘高度','4mm，与底板上表面接触'),('安装耳厚 / 螺丝','3mm / M2.5x6'),('孔深 / 旋入长度','4 / 3 mm'),('FPC缺口','宽34、高100；顶部敞开，底角R4'),('缺口至上排孔中心','左右均8mm'),('主板底面高 / 柱高 / 外径','9 / 5 / 6 mm'),('主板固定孔距','45.1 x 47.1 mm'),('主板自攻螺丝 / 底孔','M2.5x6 / 直径2.1深6'),('主板FPC','主板旋转180度，沿板面朝屏幕引出'),('底座外形','72.8 x 86 x 4 mm'),('加强筋','厚4，后缘连续曲线，中段Y=16，底部延伸至Y=46，外侧与屏幕齐平'),('主板位置','Y=15~67，后方留5mm'),('安装顺序','先固定屏幕，再装主板')]
for i,(k,v) in enumerate(rows,1):p.set('A'+str(i),k);p.set('B'+str(i),v)
p.setColumnWidth('A',300);p.setColumnWidth('B',300)
# Local screen coordinates: X across, Y upward, +Z toward display front.
base=box(-36.4,-14,0,72.8,86,4)
base=base.makeFillet(6,[e for e in base.Edges if e.BoundBox.ZLength>3.9 and e.BoundBox.XLength<.01 and e.BoundBox.YLength<.01])
base=base.makeFillet(.8,[e for e in base.Edges if e.BoundBox.ZLength<.01])
# Only the four holes nearest the connector end are used.
# Source landscape left inner column: X=129-45.5-58=25.5;
# its holes are 11.9 and 61.9 above the landscape bottom (50 apart).
screen_holes=[(-24.5,45.5),(24.5,45.5),(-25.5,103.5),(24.5,103.5)]
upright=box(-36.4,-4,-3,72.8,116,3)
upright=upright.makeFillet(4,[e for e in upright.Edges if e.BoundBox.ZLength>2.9 and e.CenterOfMass.y>111])
exit_tool=box(-17.5,12,-8,34,102,14)
exit_tool=exit_tool.makeFillet(4,[e for e in exit_tool.Edges if e.BoundBox.ZLength>13.9 and e.CenterOfMass.y<13])
upright=upright.cut(exit_tool)
upright=upright.makeFillet(.7,[e for e in upright.Edges if e.BoundBox.ZLength<.01])
for x,h in screen_holes:upright=upright.cut(cyl(x,h,-4,1.4,5))
# Reinforce only the root below the screen; retain 3 mm at screw locations.
root=box(-36.4,-4,-6,72.8,4,6)
root=root.makeFillet(.8,root.Edges)
upright=tr(upright.fuse(root)).common(box(-60,-20,0,120,130,160))
base=base.fuse(upright)
# Short lateral gussets transfer load from the low upright to the base.
# X is outside the screw-head/tool corridors and the central FPC exit.
rib_shapes=[]
for x in [-36.4,32.4]:
 low=place.multVec(V(x,1,-2))
 high=place.multVec(V(x,106,-2))
 # User-drawn C-like outline: inward waist and a smooth rearward foot.
 # Keep the return below the connector approach envelope (Z >= 8).
 waist=V(x,16,34)
 heel=V(x,16,9)
 foot=V(x,46,4)
 def bez(points):
  c=Part.BezierCurve();c.setPoles(points);return c.toShape()
 edges=[Part.makeLine(low,high),
  bez([high,V(x,high.y-1,85),V(x,16,58),waist]),
  Part.makeLine(waist,heel),
  bez([heel,V(x,16,4),V(x,30,4),foot]),
  Part.makeLine(foot,V(x,46,3)),Part.makeLine(V(x,46,3),low)]
 rib=Part.Face(Part.Wire(edges)).extrude(V(4,0,0))
 rib_shapes.append(rib)
 base=base.fuse(rib)
base=base.removeSplitter()
# Rib outer edges drop vertically from the upper attachment to the base.
# Board rotated 90 degrees: original LCD edge faces rear (+Y).
board_y=41
board_z=9
holes=[(x,board_y+y) for x in [-22.55,22.55] for y in [-23.55,23.55]]
for x,y in holes:
 base=base.fuse(cyl(x,y,3,3,board_z-3))
 base=base.cut(cyl(x,y,board_z-6,1.05,7))
# Relief stays in the ribs only: raised screw axes clear the uncut base plate.
for x,h in screen_holes[:2]:
 base=base.cut(tr(cyl(x,h,-143,3.5,140)))
# Continuous tapered ribs: lower rear edge pulled toward screen; no connector notch.
base=base.removeSplitter()
stand=obj('PrintableStand','打印件 · L型底座 · 双加强筋 · FPC开口',base,(0.26,0.58,0.65))
stand.addProperty('App::PropertyString','ManufacturingNotes')
stand.ManufacturingNotes='改用中间四孔，屏幕下边缘与底板接触；孔距按图片读数，需实物核对；耳厚3，M2.5x6旋入3；FPC口34宽100高，至上排孔中心各8；柱高5外径6。先装屏幕再装主板。'
# Screen body is only an envelope; mounting bosses meet the support plane.
screen=box(-36.4,0,5,72.8,129,5.6)
for x,h in screen_holes:
  boss=cyl(x,h,0,2.7,5).cut(cyl(x,h,0,1.25,4))
  screen=screen.fuse(boss)
screen_obj=obj('ScreenEnvelope','屏幕外形参考 · 背部器件未精确建模',tr(screen),(0.16,0.17,0.19))
glass=obj('Display','显示区域参考',tr(box(-31.14,9.34,10.6,62.28,110.32,.2)),(.06,.09,.12))
pcb=box(-25,board_y-26,board_z,50,52,1.6)
for x,y in holes:pcb=pcb.cut(cyl(x,y,board_z-1,1.4,4))
pcb_obj=obj('PCB','主板外形参考 · 元件朝上',pcb,(.12,.29,.20))
# LCD socket position inferred approximately from supplied photograph.
socket=obj('BoardLCD','主板LCD座示意 · 旋转180度后朝屏幕出线',box(0,board_y-17,board_z+1.6,23,4,3),(.82,.81,.72))
ethernet_shape=box(-27,21,board_z+1.6,21,17,14)
usb_data_shape=box(-28,39,board_z+1.6,20,7,15)
usb_power_shape=box(21,36.5,board_z+1.6,7,9,4)
ethernet=obj('EthernetEnvelope','网口包络示意 · 尺寸待实物复核',ethernet_shape,(.65,.68,.7))
usb_data=obj('USBDataEnvelope','USB数据口包络示意 · 尺寸待实物复核',usb_data_shape,(.65,.68,.7))
usb_power=obj('USBPowerEnvelope','供电USB包络示意 · 尺寸待实物复核',usb_power_shape,(.65,.68,.7))
plug_spaces={'Ethernet':box(-65,19,8,38,22,24),'USBData':box(-65,36,8,37,14,23),'USBPower':box(28,33,8,37,16,13)}
port=obj('ScreenFPC','屏幕FPC接口示意 · 旋转180度后位于上部',tr(box(-11,95,1,22,7,3)),(.82,.81,.72))
# Screen screws shown behind the rails; shaft engagement ends at local Z=3.
screws=[]
for x,h in screen_holes:screws.append(tr(cyl(x,h,-3,1.25,6).fuse(cyl(x,h,-4.8,2.25,1.8))))
for x,y in holes:screws.append(cyl(x,y,board_z-4.4,1.25,6).fuse(cyl(x,y,board_z+1.6,2.25,1.8)))
hardware=obj('Screws','螺丝参考 · 头高暂按1.8mm',Part.makeCompound(screws),(.65,.67,.70))
assert base.isValid() and len(base.Solids)==1
assert base.common(pcb).Volume<1e-6
for shape in [ethernet_shape,usb_data_shape,usb_power_shape]:assert base.common(shape).Volume<1e-6
for name,space in plug_spaces.items():assert base.common(space).Volume<1e-6,(name,'plug approach obstructed')
assert base.common(tr(screen)).Volume<1e-6
contact_gap=base.distToShape(tr(screen))[0]
assert contact_gap<1e-6
assert abs(place.multVec(V(0,0,5)).z-4)<1e-9
assert base.common(tr(exit_tool)).Volume<1e-6
assert abs((-17.5)-screen_holes[2][0]-8)<1e-9
assert abs(screen_holes[3][0]-16.5-8)<1e-9
assert base.common(port.Shape).Volume<1e-6
outside_envelope=base.cut(box(-36.4,-14,0,72.8,86,180)).Volume
print('Outside exact base envelope:',outside_envelope,flush=True)
assert outside_envelope<1e-5
# No screw clearance cuts or openings anywhere in the flat central underside.
bottom_probe=box(-29,-7,0,58,72,.1)
assert bottom_probe.cut(base).Volume<1e-6
uncut_plate=box(-36.4,-14,0,72.8,86,4)
for x,h in screen_holes[:2]:assert uncut_plate.common(tr(cyl(x,h,-143,3.5,139.9))).Volume<1e-6
for x,h in screen_holes:
 assert abs(base.common(tr(cyl(x,h,-4.8,2.25,1.8))).Volume)<1e-6
 # 6 mm diameter screwdriver access for 25 mm behind each bearing face.
 assert base.common(tr(cyl(x,h,-143,3,139.9))).Volume<1e-6
mesh=MeshPart.meshFromShape(Shape=base,LinearDeflection=.06,AngularDeflection=.15,Relative=False)
assert mesh.isSolid()
mesh.write(str(PRINT/'L型底座_中间四孔.stl'))
Part.export([stand],str(MODELS/'L型底座_中间四孔.step'))
d.recompute();d.saveAs(str(MODELS/'L型底座_中间四孔_屏幕落底.FCStd'))
report={'valid':base.isValid(),'solid_count':len(base.Solids),'closed_mesh':mesh.isSolid(),'base_pcb_overlap':base.common(pcb).Volume,'base_screen_overlap':base.common(tr(screen)).Volume,'screen_screw_engagement':3,'screen_hole_depth':4,'pcb_assumed_thickness':1.6,'pcb_bottom_height':board_z,'standoff_height':board_z-4,'standoff_outer_diameter':6,'pilot_radial_wall':1.95,'pilot_bottom_above_base':board_z-6-4,'screw_tip_to_pilot_bottom':1.6,'pcb_screw_engagement':4.4,'pcb_pilot_depth':6,'screen_middle_four_holes':screen_holes,'fpc_exit_width':34,'upper_hole_to_exit_side_mm':[8,8],'exit_x_limits':[-17.5,16.5],'fpc_exit_height':100,'fpc_exit_interference':base.common(tr(exit_tool)).Volume,'FPC':'screen rotated 180 degrees, FPC high; PCB rotated 180 degrees, FPC toward screen; cable length and connector contact orientation unverified'}
report['ribs']={'count':2,'thickness_mm':4,'top_z_mm':high.z,'rear_y_mm':46,'outer_edge_vertical':False,'curved_C_outline':True,'waist_y':16,'waist_z':[9,34],'screen_screw_tool_clearance_diameter_mm':6,'checked_tool_length_mm':140}
report['rounding']={'base_corner_R':6,'base_edges_R':.8,'upright_top_R':4,'FPC_bottom_corner_R':4,'upright_edge_R':.7,'rib_tip_R':0,'rib_edge_R':0,'rib_base_and_upright_blend_R':0}
report['lower_screw_access']={'rib_relief_diameter':7,'base_slots':False,'approach_length':140,'assembly':'screen first, then PCB; driver handle envelope not modeled'}
report['orientation']={'screen_in_plane_rotation_deg':180,'pcb_in_plane_rotation_deg':180,'screen_FPC':'upper','pcb_FPC':'toward screen'}
report['screen_contact_gap']=contact_gap
report['connector_access']={'dimensions_source':'conservative photo estimates; physical check required','notch':False,'rib_lower_rear_y':46,'lower_return_below_connectors':True,'solid_overlap_mm3':{name:base.common(space).Volume for name,space in plug_spaces.items()},'power_USB_side':'+X','ethernet_and_data_USB_side':'-X'}
report['layout']={'base_width':72.8,'base_depth':86,'rear_margin_behind_pcb':5,'rib_outer_x':[-36.4,36.4],'screen_bottom_height':4,'screen_mount_origin_z':screen_origin_z,'pcb_shift_toward_screen':16,'pcb_y_limits':[15,67],'outside_exact_base_envelope_volume':outside_envelope,'bottom_probe_missing_volume':bottom_probe.cut(base).Volume}
(REPORTS/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
# CAD tessellation preview, not an AI-generated rendering.
os.environ['MPLCONFIGDIR']='/private/tmp/screen_stand_mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig=plt.figure(figsize=(13,8),facecolor='#f4f6f8')
for j,az in [(1,-65),(2,120)]:
 ax=fig.add_subplot(1,2,j,projection='3d');ax.set_facecolor('#f4f6f8')
 all_faces=[];all_colors=[]
 for o in ([stand,pcb_obj,socket,ethernet,usb_data,usb_power] if j==1 else [stand,screen_obj,glass,pcb_obj,socket,port,hardware,ethernet,usb_data,usb_power]):
  m=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.16,AngularDeflection=.25,Relative=False)
  vs,fs=m.Topology;v=np.array([[v.x,v.y,v.z] for v in vs]);faces=v[np.array(fs)]
  # Smaller coplanar triangles avoid painter-sort artifacts across large faces.
  pending=list(faces);fine=[]
  while pending:
   tri=pending.pop();a,b,c=tri
   if max(np.linalg.norm(a-b),np.linalg.norm(b-c),np.linalg.norm(c-a))>10:
    ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
    pending.extend([np.array([a,ab,ca]),np.array([ab,b,bc]),np.array([ca,bc,c]),np.array([ab,bc,ca])])
   else:fine.append(tri)
  faces=np.array(fine)
  all_faces.extend(faces);all_colors.extend([tuple(o.PreviewColor[:3])]*len(faces))
 ax.add_collection3d(Poly3DCollection(all_faces,facecolors=all_colors,linewidths=0,antialiased=False,shade=True,lightsource=LightSource(azdeg=300,altdeg=50)))
 ax.set(xlim=(-42,42),ylim=(-20,77),zlim=(0,140 if j==2 else 125));ax.set_box_aspect((84,97,140 if j==2 else 125));ax.view_init(elev=25,azim=120);ax.set_axis_off();ax.set_title('L BRACKET / CURVED RIBS' if j==1 else 'ASSEMBLY / SCREEN ON BASE',fontsize=12)
fig.subplots_adjust(0,0,1,.94,0,0);fig.savefig(PREVIEWS/'preview.png',dpi=160)
print(json.dumps(report,ensure_ascii=False))
