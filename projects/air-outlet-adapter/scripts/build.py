"""Execute in FreeCAD's Python console with exec(compile(...))."""
from pathlib import Path
import json, math
import FreeCAD as A, Part, Sketcher, MeshPart

ROOT = Path(__file__).resolve().parents[1]
for folder in ('models', 'print', 'previews', 'reports'):
    (ROOT / folder).mkdir(exist_ok=True)
if A.getDocument('AirAdapter'):
    A.closeDocument('AirAdapter')
d = A.newDocument('AirAdapter')
d.Label = '出风口转接'
p = d.addObject('Spreadsheet::Sheet', 'Params'); p.Label = '参数'
for col, title in zip('ABCD', ['参数', '数值', '单位', '说明']):
    p.set(col+'1', title)
rows = [('矩形长边',56,'Width','用户指定外尺寸'),('矩形短边',28,'Height','用户指定外尺寸'),('圆口外径',65,'Diameter','用户指定外尺寸'),('总长',60,'Length','矩形10 + 过渡30 + 圆口20'),('端口壁厚',2,'Wall','直口径向壁厚；过渡段为内外轮廓放样'),('矩形直口长',10,'RectLength','默认值'),('圆形直口长',20,'RoundLength','默认值'),('矩形外圆角',2.5,'Corner','用户指定 R2.5'),('限位伸出',2,'StopWidth','单侧伸出'),('限位厚度',1.5,'StopThickness','轴向厚度'),('限位斜坡长',4,'RampLength','圆口朝下打印'),('缩径外径',63,'WaistDiameter','圆口中间段'),('缩径长度',13,'WaistLength','包含两侧斜坡，轴向居中'),('缩径斜坡长',1,'WaistRamp','每侧轴向1 mm，径向1 mm，45度')]
for i,(label,value,alias,note) in enumerate(rows,2):
    p.set('A'+str(i),label);p.set('B'+str(i),str(value));p.setAlias('B'+str(i),alias)
    p.set('C'+str(i),'mm');p.set('D'+str(i),note)
p.set('A17','驱动方式');p.set('D17','数值通过表达式驱动草图和特征；尺寸表达式乘以 1 mm')
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
    e1=extrusion(prefix+'RectTube',label+'矩形直口',a,'Params.RectLength',True)
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
final=d.addObject('Part::Cut','Adapter');final.Label='转接头';final.Base=waist;final.Tool=inner;final.Refine=True
d.recompute()
assert final.Shape.isValid() and len(final.Shape.Solids)==1
v=final.Shape.Volume
p.set('B5','61');d.recompute()
assert final.Shape.isValid() and abs(final.Shape.BoundBox.ZLength-61)<1e-5 and abs(final.Shape.Volume-v)>1
p.set('B5','60');d.recompute()
assert abs(final.Shape.BoundBox.ZLength-60)<1e-5
# Check both end lands, central waist, and the continuous circular bore.
for z,diameter in [(42,65),(44,64),(44.5,63),(50,63),(55.5,63),(56,64),(58,65)]:
    section=final.Shape.section(Part.makePlane(100,100,V(-50,-50,z)))
    assert abs(section.BoundBox.XLength-diameter)<1e-5
    assert final.Shape.isInside(V(30.5,0,z),1e-6,True)
    assert not final.Shape.isInside(V(29,0,z),1e-6,True)
assert not final.Shape.isInside(V(0,0,25),1e-6,True)
printshape=final.Shape.copy()
printshape.Placement=A.Placement(V(0,0,float(p.Length)),A.Rotation(V(1,0,0),180))
mesh=MeshPart.meshFromShape(Shape=printshape,LinearDeflection=0.08,AngularDeflection=0.12,Relative=False)
assert mesh.isSolid()
mesh.write(str(ROOT/'print/转接头.stl'))
Part.export([final],str(ROOT/'models/转接头.step'))
for o in d.Objects:
    if o.ViewObject:o.Visibility=False
final.Visibility=True
final.ViewObject.ShapeColor=(0.78,0.83,0.88);final.ViewObject.LineColor=(0.20,0.25,0.30)
final.ViewObject.DisplayMode='Flat Lines'
report={'valid':final.Shape.isValid(),'solids':len(final.Shape.Solids),'volume_mm3':final.Shape.Volume,'mesh_closed':mesh.isSolid(),'parameter_recompute':True,'round_sections_mm':[[42,65],[44,64],[50,63],[56,64],[58,65]],'bore_mm':59,'minimum_round_wall_mm':2,'waist_ramp_mm':1,'waist_flat_mm':11,'ramp_sections_verified':True}
(ROOT/'reports/check.json').write_text(json.dumps(report,indent=2))
if A.GuiUp:
    import FreeCADGui as G
    G.Selection.clearSelection();G.activeDocument().activeView().viewAxonometric();G.activeDocument().activeView().fitAll()
    view=G.activeDocument().activeView()
    view.setCameraOrientation(view.getCameraOrientation().multiply(A.Rotation(V(1,0,0),180)).Q)
    view.fitAll()
    G.activeDocument().activeView().saveImage(str(ROOT/'previews/转接头.png'),1200,1000,'White')
d.recompute();d.saveAs(str(ROOT/'models/出风口转接.FCStd'))
print('ADAPTER_COMPLETE',report)
