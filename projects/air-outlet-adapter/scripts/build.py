"""Execute in FreeCAD's Python console with exec(compile(...))."""
from pathlib import Path
import json, math
import FreeCAD as A, Part, Sketcher, MeshPart

ROOT = Path(__file__).resolve().parents[1]
for folder in ('models', 'print', 'previews', 'reports'):
    (ROOT / folder).mkdir(exist_ok=True)
if 'AirAdapter' in A.listDocuments():
    A.closeDocument('AirAdapter')
d = A.newDocument('AirAdapter')
d.Label = '出风口转接'
p = d.addObject('Spreadsheet::Sheet', 'Params'); p.Label = '参数'
for col, title in zip('ABCD', ['参数', '数值', '单位', '说明']):
    p.set(col+'1', title)
rows = [('矩形长边',56,'Width','用户指定外尺寸'),('矩形短边',28,'Height','用户指定外尺寸'),('圆口外径',65,'Diameter','用户指定外尺寸'),('基础长',60,'Length','原口沿至圆口；不含新增延伸'),('端口壁厚',2,'Wall','直口径向壁厚；过渡段为内外轮廓放样'),('矩形直口长',10,'RectLength','默认值'),('圆形直口长',20,'RoundLength','默认值'),('矩形外圆角',2.5,'Corner','用户指定 R2.5'),('限位伸出',2,'StopWidth','单侧伸出'),('限位厚度',1.5,'StopThickness','轴向厚度'),('限位斜坡长',4,'RampLength','圆口朝下打印'),('缩径外径',63,'WaistDiameter','圆口中间段'),('缩径长度',13,'WaistLength','包含两侧斜坡，轴向居中'),('缩径斜坡长',1,'WaistRamp','每侧轴向1 mm，径向1 mm，45度'),('方口延伸',20,'Extension','原口沿向上延伸'),('参考圆半径',50,'GuideRadius','长边侧视切口圆弧'),('圆心偏移',60,'GuideOffset','从限位肩右端向左及向上各60'),('口沿倒角',1.2,'LipChamfer','记录值；原生倒角特征可编辑，脚本重建读取此值')]
for i,(label,value,alias,note) in enumerate(rows,2):
    p.set('A'+str(i),label);p.set('B'+str(i),str(value));p.setAlias('B'+str(i),alias)
    p.set('C'+str(i),'mm');p.set('D'+str(i),note)
p.set('A23','驱动方式');p.set('D23','除口沿倒角为记录值外，其余数值通过表达式驱动草图和特征')
p.setColumnWidth('A',150);p.setColumnWidth('B',90);p.setColumnWidth('C',70);p.setColumnWidth('D',350)
d.recompute()
V=A.Vector
def expr(s,c,e): s.setExpression('Constraints[%d]'%c,'('+e+') * 1 mm')
def profile(name,label,inner,round_,z,stop=False):
    s=d.addObject('Sketcher::SketchObject',name);s.Label=label
    s.setExpression('Placement.Base.z','('+z+') * 1 mm')
    sub=' - 2 * Params.Wall' if inner else ''
    if round_:
        idx=s.addGeometry(Part.Circle(V(0,0,0),V(0,0,1),28 if inner else 30),False)
        s.addConstraint(Sketcher.Constraint('Coincident',idx,3,-1,1))
        c=s.addConstraint(Sketcher.Constraint('Diameter',idx,56 if inner else 60));expr(s,c,('Params.WaistDiameter' if inner else 'Params.Diameter')+sub)
    else:
        extra=' + 2 * Params.StopWidth' if stop else ''
        w,h=(52,24) if inner else ((60,32) if stop else (56,28))
        r=0.5 if inner else (4.5 if stop else 2.5)
        we='(Params.Width'+sub+extra+') / 2'
        he='(Params.Height'+sub+extra+') / 2'
        re='Params.Corner'+(' - Params.Wall' if inner else (' + Params.StopWidth' if stop else ''))
        # Four independent dimensioned arcs and lines form an exact closed wire.
        for j,(sx,sy,a0) in enumerate([(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]):
            cx,cy=sx*(w/2-r),sy*(h/2-r)
            idx=s.addGeometry(Part.ArcOfCircle(Part.Circle(V(cx,cy,0),V(0,0,1),r),math.radians(a0),math.radians(a0+90)),False)
            for kind,pt,val,ex in [('DistanceX',3,cx,f'{sx} * ({we} - ({re}))'),('DistanceY',3,cy,f'{sy} * ({he} - ({re}))')]:
                c=s.addConstraint(Sketcher.Constraint(kind,idx,pt,val));expr(s,c,ex)
            c=s.addConstraint(Sketcher.Constraint('Radius',idx,r));expr(s,c,re)
            s.addConstraint(Sketcher.Constraint('Horizontal' if j%2==0 else 'Vertical',idx,3,idx,1))
            s.addConstraint(Sketcher.Constraint('Vertical' if j%2==0 else 'Horizontal',idx,3,idx,2))
        for j in range(4):
            start=s.Geometry[j].EndPoint;end=s.Geometry[(j+1)%4].StartPoint
            idx=s.addGeometry(Part.LineSegment(start,end),False)
            s.addConstraint(Sketcher.Constraint('Coincident',idx,1,j,2))
            s.addConstraint(Sketcher.Constraint('Coincident',idx,2,(j+1)%4,1))
    d.recompute();return s
def extrusion(name,label,s,length,reverse=False):
    f=d.addObject('Part::Extrusion',name);f.Label=label;f.Base=s;f.DirMode='Normal';f.Solid=True
    f.setExpression('LengthFwd','('+length+') * 1 mm');f.Reversed=reverse
    d.recompute();return f
def shell_volume(prefix,inner):
    label='内' if inner else '外'
    a=profile(prefix+'Rect',label+'矩形',inner,False,'Params.RectLength')
    b=profile(prefix+'Circle',label+'圆形',inner,True,'Params.Length - Params.RoundLength')
    lo=d.addObject('Part::Loft',prefix+'Loft');lo.Label=label+'过渡';lo.Sections=[a,b];lo.Solid=True;lo.Ruled=False
    e1=extrusion(prefix+'RectTube',label+'矩形直口',a,'Params.RectLength + Params.Extension',True)
    e2=extrusion(prefix+'RoundTube',label+'圆形直口',b,'Params.RoundLength')
    f=d.addObject('Part::MultiFuse',prefix+'Union');f.Label=label+'合并';f.Shapes=[lo,e1,e2];f.Refine=True;d.recompute()
    return f
outer=shell_volume('Outer',False);inner=shell_volume('Inner',True)
shoulder=profile('StopProfile','限位轮廓',False,False,'Params.RectLength',True)
lip=extrusion('StopLip','限位肩',shoulder,'Params.StopThickness')
wide=profile('RampWide','斜坡外沿',False,False,'Params.RectLength + Params.StopThickness',True)
root=profile('RampRoot','斜坡根部',False,False,'Params.RectLength + Params.StopThickness + Params.RampLength')
ramp=d.addObject('Part::Loft','StopRamp');ramp.Label='限位斜坡';ramp.Sections=[wide,root];ramp.Solid=True;ramp.Ruled=True
joined=d.addObject('Part::MultiFuse','StoppedOuter');joined.Label='限位合并';joined.Shapes=[outer,lip,ramp];joined.Refine=True;d.recompute()
groove=d.addObject('Sketcher::SketchObject','WaistProfile');groove.Label='缩径轮廓'
groove.setExpression('Placement.Base.z','(Params.Length - (Params.RoundLength + Params.WaistLength) / 2) * 1 mm')
for radius,expression in [(34.5,'Params.Diameter + 4')]:
    idx=groove.addGeometry(Part.Circle(V(0,0,0),V(0,0,1),radius),False)
    groove.addConstraint(Sketcher.Constraint('Coincident',idx,3,-1,1))
    c=groove.addConstraint(Sketcher.Constraint('Diameter',idx,2*radius));expr(groove,c,expression)
blank=extrusion('WaistBlank','缩径包络',groove,'Params.WaistLength')
sections=[]
z0='Params.Length - (Params.RoundLength + Params.WaistLength) / 2'
for i,(offset,diameter) in enumerate([('0','Params.Diameter'),('Params.WaistRamp','Params.WaistDiameter'),('Params.WaistLength - Params.WaistRamp','Params.WaistDiameter'),('Params.WaistLength','Params.Diameter')]):
    s=d.addObject('Sketcher::SketchObject','WaistSection'+str(i+1));s.Label='缩径截面'+str(i+1)
    s.setExpression('Placement.Base.z','('+z0+' + '+offset+') * 1 mm')
    idx=s.addGeometry(Part.Circle(V(0,0,0),V(0,0,1),32),False)
    s.addConstraint(Sketcher.Constraint('Coincident',idx,3,-1,1))
    c=s.addConstraint(Sketcher.Constraint('Diameter',idx,64));expr(s,c,diameter)
    sections.append(s)
core=d.addObject('Part::Loft','WaistCore');core.Label='缩径斜坡';core.Sections=sections;core.Solid=True;core.Ruled=True
tool=d.addObject('Part::Cut','WaistTool');tool.Label='缩径切除体';tool.Base=blank;tool.Tool=core;tool.Refine=True
d.recompute()
waist=d.addObject('Part::Cut','Waist');waist.Label='圆口缩径';waist.Base=joined;waist.Tool=tool;waist.Refine=True
shell=d.addObject('Part::Cut','Hollow');shell.Label='风道';shell.Base=waist;shell.Tool=inner;shell.Refine=True
arc=d.addObject('Sketcher::SketchObject','GuideCircle');arc.Label='口沿圆弧'
arc.Placement=A.Placement(V(0,20,0),A.Rotation(V(1,0,0),90))
arc.setExpression('Placement.Base.y','(Params.Height / 2 + Params.StopWidth + 4) * 1 mm')
idx=arc.addGeometry(Part.Circle(V(-30,-50,0),V(0,0,1),50),False)
for typ,val,ex in [('DistanceX',-30,'Params.Width / 2 + Params.StopWidth - Params.GuideOffset'),('DistanceY',-50,'Params.RectLength - Params.GuideOffset')]:
    c=arc.addConstraint(Sketcher.Constraint(typ,idx,3,val));expr(arc,c,ex)
c=arc.addConstraint(Sketcher.Constraint('Radius',idx,50));expr(arc,c,'Params.GuideRadius')
arc_tool=extrusion('ArcTool','圆弧切除体',arc,'Params.Height + 2 * Params.StopWidth + 8')
trim=d.addObject('Part::Cut','Trim');trim.Label='弧形口沿';trim.Base=shell;trim.Tool=arc_tool;trim.Refine=True
d.recompute()
# Find the inner perimeter edges at the upper opening for a native chamfer.
inner_faces=[]
for f in trim.Shape.Faces:
    bb=f.BoundBox
    if bb.ZMin < -0.001 and bb.ZMax > 9.9 and (abs(abs(bb.XMin)-26)<1e-5 and bb.XLength<1e-5 or abs(abs(bb.YMin)-12)<1e-5 and bb.YLength<1e-5 or (bb.XMin>=-26.0001 and bb.XMax<=26.0001 and bb.YMin>=-12.0001 and bb.YMax<=12.0001 and bb.XLength<1 and bb.YLength<1)):
        inner_faces.append(f)
edges=[]
for i,e in enumerate(trim.Shape.Edges,1):
    if e.BoundBox.ZMax<0.1 and any(any(e.isSame(fe) for fe in f.Edges) for f in inner_faces):
        edges.append(i)
final=d.addObject('Part::Chamfer','Adapter');final.Label='转接头';final.Base=trim
final.Edges=[(i,float(p.LipChamfer),float(p.LipChamfer)) for i in edges]
print('LIP_EDGES',edges)
d.recompute()
assert final.Shape.isValid() and len(final.Shape.Solids)==1
v=final.Shape.Volume
p.set('B5','61');d.recompute()
assert final.Shape.isValid() and abs(final.Shape.BoundBox.ZLength-81)<1e-5 and abs(final.Shape.Volume-v)>1
p.set('B5','60');d.recompute()
assert abs(final.Shape.BoundBox.ZLength-80)<1e-5
p.set('B17','49.9');d.recompute()
assert final.Shape.isValid() and len(final.Shape.Solids)==1 and abs(final.Shape.Volume-v)>0.01
p.set('B17','50');d.recompute()
assert final.Shape.isValid() and final.Shape.common(arc_tool.Shape).Volume<1e-6
assert final.Shape.Volume<trim.Shape.Volume
assert final.Shape.isInside(V(20,13.4,-19.99),1e-6,True)
assert not final.Shape.isInside(V(20,12.8,-19.99),1e-6,True)
assert abs(final.Shape.BoundBox.ZMin+20)<1e-5
# Check both end lands, central waist, and the continuous circular bore.
for z,diameter in [(42,65),(44,64),(44.5,63),(50,63),(55.5,63),(56,64),(58,65)]:
    section=final.Shape.section(Part.makePlane(100,100,V(-50,-50,z)))
    assert abs(section.BoundBox.XLength-diameter)<1e-5
    assert final.Shape.isInside(V(30.5,0,z),1e-6,True)
    assert not final.Shape.isInside(V(29,0,z),1e-6,True)
assert not final.Shape.isInside(V(0,0,25),1e-6,True)
# Place the finished feature in the shared model/STEP/STL coordinates:
# round mouth on Z=0, rectangular mouth upwards. Keep native upstream history.
final.Placement=A.Placement(V(0,0,float(p.Length)),A.Rotation(V(1,0,0),180))
final.setExpression('Placement.Base.z','Params.Length * 1 mm')
d.recompute()
assert final.Shape.isValid() and len(final.Shape.Solids)==1
assert abs(final.Shape.BoundBox.ZMin)<1e-5 and abs(final.Shape.BoundBox.ZMax-80)<1e-5
bottom=final.Shape.section(Part.makePlane(100,100,V(-50,-50,1)))
assert abs(bottom.BoundBox.XLength-65)<1e-5 and abs(bottom.BoundBox.YLength-65)<1e-5
p.set('B5','61');d.recompute()
assert final.Shape.isValid() and abs(final.Shape.BoundBox.ZMin)<1e-5 and abs(final.Shape.BoundBox.ZMax-81)<1e-5
p.set('B5','60');d.recompute()
printshape=final.Shape.copy()
mesh=MeshPart.meshFromShape(Shape=printshape,LinearDeflection=0.08,AngularDeflection=0.12,Relative=False)
assert mesh.isSolid()
mesh.write(str(ROOT/'print/转接头.stl'))
Part.export([final],str(ROOT/'models/转接头.step'))
for o in d.Objects:
    if o.ViewObject:o.Visibility=False
final.Visibility=True
final.ViewObject.ShapeColor=(0.78,0.83,0.88);final.ViewObject.LineColor=(0.20,0.25,0.30)
final.ViewObject.DisplayMode='Flat Lines'
report={'valid':final.Shape.isValid(),'solids':len(final.Shape.Solids),'volume_mm3':final.Shape.Volume,'mesh_closed':mesh.isSolid(),'parameter_recompute':True,'round_sections_mm':[[42,65],[44,64],[50,63],[56,64],[58,65]],'bore_mm':59,'minimum_round_wall_mm':2,'waist_ramp_mm':1,'waist_flat_mm':11,'extension_mm':20,'guide_radius_mm':50,'lip_chamfer_mm':1.2,'ramp_sections_verified':True,'round_mouth_down':True,'bottom_z_mm':final.Shape.BoundBox.ZMin,'overall_height_mm':final.Shape.BoundBox.ZLength}
(ROOT/'reports/check.json').write_text(json.dumps(report,indent=2))
d.recompute();d.saveAs(str(ROOT/'models/出风口转接.FCStd'))
if A.GuiUp:
    import FreeCADGui as G
    from PySide import QtCore
    def finish_view():
        path=ROOT/'scripts/final_view.py'
        exec(compile(path.read_text(),str(path),'exec'),{'__file__':str(path)})
    QtCore.QTimer.singleShot(300,finish_view)
print('ADAPTER_COMPLETE',report)
