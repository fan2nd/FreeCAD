"""Execute with runpy.run_path in FreeCAD's Python console."""
from pathlib import Path
import json
import FreeCAD as A, Part, Sketcher
ROOT=Path(__file__).resolve().parents[1]
V=A.Vector
for sub in ('models','previews','reports'):(ROOT/sub).mkdir(exist_ok=True)
d=A.newDocument('HT2806');d.Label='HT2806'
p=d.addObject('Spreadsheet::Sheet','Params');p.Label='尺寸参数'
rows=[
('外径',34.6,'OD','图纸'),('后端直径',33.5,'RearD','图纸'),
('机身厚',15,'Length','图纸，不含凸台'),('后端台阶厚',1,'Step','图纸淡字按1读取'),
('磁铁直径',12,'BossD','图纸；用户确认凸台为磁铁'),('磁铁高',3,'BossH','图纸；用户确认凸台为磁铁'),
('中心孔径',4.5,'Bore','图纸；贯通为假设'),('前端沉孔径',6.4,'CounterD','图纸'),
('后孔横距',16,'RearX','图纸'),('后孔纵距',20.5,'RearY','图纸'),
('后双孔分布圆',29.5,'RearPCD','图纸，沿Y方向'),('前方孔距',10.5,'FrontPitch','图纸'),
('前四孔分布圆',12.5,'FrontPCD','图纸，沿X/Y方向'),
('M2简化孔径',2,'ThreadSmall','名义直径光孔，不生成牙型'),('M2.5简化孔径',2.5,'ThreadLarge','名义直径光孔，不生成牙型'),
('安装孔深',3,'HoleDepth','未标注，暂取3'),('沉孔深',0.5,'CounterDepth','未标注，暂取0.5'),
('后环位置',4,'BandZ','按图比例暂取'),('前环位置',14,'FrontZ','按图比例暂取'),
('环槽宽',0.2,'SeamW','外观假设'),('环槽深',0.15,'SeamD','外观假设'),
('出线槽左边',-14,'WireX','图示矩形按比例暂取'),('出线槽宽',6,'WireW','未标注'),
('出线槽高',12,'WireH','未标注'),('出线槽深',0.5,'WireDepth','未标注，暂作浅槽')]
for c,t in zip('ABCD',('参数','数值','单位','说明')):p.set(c+'1',t)
for i,(label,val,alias,note) in enumerate(rows,2):
    p.set('A'+str(i),label);p.set('B'+str(i),str(val));p.setAlias('B'+str(i),alias);p.set('C'+str(i),'mm');p.set('D'+str(i),note)
p.setColumnWidth('A',150);p.setColumnWidth('B',80);p.setColumnWidth('C',60);p.setColumnWidth('D',300)
n=d.addObject('Spreadsheet::Sheet','Notes');n.Label='说明'
notes=['尺寸参数表驱动几何；所有数值单位均独立列出。','电机安装外形作为一个实体；用户确认后端Ø12×3凸台为磁铁，不推定其余内部结构。','Z=0 为凸台侧机身端面，机身至Z=15，凸台至Z=-3；总长18。','凸台侧：4×M2，16×20.5矩形；2×M2.5，Ø29.5分布圆上下两孔。','另一侧：4×M2.5，10.5×10.5正方形；4×M2，Ø12.5分布圆四等分。','螺纹均用名义直径圆柱盲孔表达，孔深3为假设；不得据此确定螺钉最大旋入深度。','Ø4.5按中心通孔、Ø6.4按前端浅沉孔理解；原图未给剖面，待实物确认。','环槽、矩形出线浅槽和孔深按外观补全；无公差、材料和制造细节定义。']
for i,t in enumerate(notes,1):n.set('A'+str(i),t)
n.setColumnWidth('A',850)
d.recompute()
b=d.addObject('PartDesign::Body','Motor');b.Label='电机'
def sk(name,label,z='0 mm'):
    s=b.newObject('Sketcher::SketchObject',name);s.Label=label;s.setExpression('Placement.Base.z',z);return s
def circle(s,x,y,r,xe=None,ye=None,re=None):
    g=s.addGeometry(Part.Circle(V(x,y,0),V(0,0,1),r),False)
    for axis,value,ex in [('DistanceX',x,xe),('DistanceY',y,ye)]:
        if value==0 and ex is None:
            s.addConstraint(Sketcher.Constraint('DistanceX' if axis=='DistanceX' else 'DistanceY',g,3,0.0))
        else:
            c=s.addConstraint(Sketcher.Constraint(axis,g,3,value))
            if ex:s.setExpression('Constraints[%d]'%c,ex)
    c=s.addConstraint(Sketcher.Constraint('Radius',g,r))
    if re:s.setExpression('Constraints[%d]'%c,re)
def feature(s,name,label,typ,length,rev=False):
    f=b.newObject('PartDesign::'+typ,name);f.Label=label;f.Profile=s;f.setExpression('Length',length);f.Reversed=rev;f.Refine=True
    d.recompute()
    assert not f.Shape.isNull() and f.Shape.isValid(),(name,f.State)
    for o in b.Group:o.Visibility=False
    f.Visibility=True
    return f
def disk(name,label,z,r,re,length,rev=False):
    s=sk(name+'Sketch',label+'轮廓',z);circle(s,0,0,r,re=re)
    return feature(s,name,label,'Pad',length,rev)
disk('Rear','后端','0 mm',16.75,'Params.RearD / 2 * 1 mm','Params.Step * 1 mm')
disk('Shell','机壳','Rear.Length',17.3,'Params.OD / 2 * 1 mm','Params.Length * 1 mm - Rear.Length')
disk('Boss','定位凸台','0 mm',6,'Params.BossD / 2 * 1 mm','Params.BossH * 1 mm',True)
for name,zz in [('RearSeam','Params.BandZ'),('FrontSeam','Params.FrontZ')]:
    s=sk(name+'Sketch','环槽轮廓',zz+' * 1 mm')
    circle(s,0,0,18,re='(Params.OD / 2 + 1) * 1 mm')
    circle(s,0,0,17.15,re='(Params.OD / 2 - Params.SeamD) * 1 mm')
    feature(s,name,'后环槽' if name=='RearSeam' else '前环槽','Pocket','Params.SeamW * 1 mm',True)
s=sk('BoreSketch','中心孔轮廓','(Params.Length) * 1 mm');circle(s,0,0,2.25,re='Params.Bore / 2 * 1 mm')
feature(s,'Bore','中心孔','Pocket','(Params.Length + Params.BossH) * 1 mm')
s=sk('CounterSketch','沉孔轮廓','Params.Length * 1 mm');circle(s,0,0,3.2,re='Params.CounterD / 2 * 1 mm')
feature(s,'Counter','中心沉孔','Pocket','Params.CounterDepth * 1 mm')
for side in ('Rear','Front'):
    s=sk(side+'MountSketch','后安装孔位' if side=='Rear' else '前安装孔位','0 mm' if side=='Rear' else 'Params.Length * 1 mm')
    for sx in (-1,1):
        for sy in (-1,1):
            px,py,diam=(8,10.25,2) if side=='Rear' else (5.25,5.25,2.5)
            circle(s,sx*px,sy*py,diam/2,('%s * Params.RearX / 2 * 1 mm'%sx) if side=='Rear' else '%s * Params.FrontPitch / 2 * 1 mm'%sx,('%s * Params.RearY / 2 * 1 mm'%sy) if side=='Rear' else '%s * Params.FrontPitch / 2 * 1 mm'%sy,'Params.%s / 2 * 1 mm'%('ThreadSmall' if side=='Rear' else 'ThreadLarge'))
    feature(s,side+'Mount','后安装孔' if side=='Rear' else '前安装孔','Pocket','Params.HoleDepth * 1 mm',side=='Rear')
    s=sk(side+'PCDSketch','后双孔位' if side=='Rear' else '前四孔位','0 mm' if side=='Rear' else 'Params.Length * 1 mm')
    points=[(0,-1),(0,1)] if side=='Rear' else [(0,-1),(0,1),(-1,0),(1,0)]
    rad=14.75 if side=='Rear' else 6.25
    for x,y in points:circle(s,x*rad,y*rad,1.25 if side=='Rear' else 1,('%s * Params.%sPCD / 2 * 1 mm'%(x,side)) if x else None,('%s * Params.%sPCD / 2 * 1 mm'%(y,side)) if y else None,'Params.%s / 2 * 1 mm'%('ThreadLarge' if side=='Rear' else 'ThreadSmall'))
    feature(s,side+'PCD','后双孔' if side=='Rear' else '前四孔','Pocket','Params.HoleDepth * 1 mm',side=='Rear')
s=sk('WireSketch','出线槽轮廓')
pts=[(-14,-6),(-8,-6),(-8,6),(-14,6)]
expressions=[('Params.WireX','-Params.WireH/2'),('Params.WireX+Params.WireW','-Params.WireH/2'),('Params.WireX+Params.WireW','Params.WireH/2'),('Params.WireX','Params.WireH/2')]
for i in range(4):
    j=s.addGeometry(Part.LineSegment(V(*pts[i],0),V(*pts[(i+1)%4],0)),False)
    for point,k in [(1,i),(2,(i+1)%4)]:
        for axis,value,expr in zip(('DistanceX','DistanceY'),pts[k],expressions[k]):
            c=s.addConstraint(Sketcher.Constraint(axis,j,point,value));s.setExpression('Constraints[%d]'%c,'('+expr+') * 1 mm')
feature(s,'Wire','出线槽','Pocket','Params.WireDepth * 1 mm',True)
d.recompute()
assert len(b.Shape.Solids)==1 and b.Shape.isValid()
assert abs(b.Shape.BoundBox.ZLength-18)<1e-7
assert abs(d.ShellSketch.Geometry[0].Radius * 2 - 34.6)<1e-7
assert any(hasattr(f.Surface,'Radius') and abs(f.Surface.Radius-17.3)<1e-7 for f in b.Shape.Faces)
# Check parameter propagation and restore the drawing value before export.
p.set('B4','16');d.recompute();assert abs(b.Shape.BoundBox.ZLength-19)<1e-7 and b.Shape.isValid()
p.set('B4','15');d.recompute()
assert not [o.Name for o in d.Objects if 'Invalid' in o.State]
report={'valid':b.Shape.isValid(),'solids':len(b.Shape.Solids),'outer_diameter_mm':d.ShellSketch.Geometry[0].Radius*2,'overall_length_mm':b.Shape.BoundBox.ZLength,'parameter_recompute':True,'sketches':len([o for o in d.Objects if o.TypeId=='Sketcher::SketchObject'])}
(ROOT/'reports/check.json').write_text(json.dumps(report,indent=2))
Part.export([b],str(ROOT/'models/HT2806.step'))
if A.GuiUp:
    import FreeCADGui as G
    from PySide import QtWidgets
    G.activateWorkbench('PartWorkbench')
    b.ViewObject.ShapeColor=(0.72,0.75,0.8);b.Tip.ViewObject.ShapeColor=(0.72,0.75,0.8)
    b.Tip.ViewObject.LineColor=(0.18,0.2,0.24)
    G.Selection.clearSelection();v=G.activeDocument().activeView();v.viewAxonometric();v.fitAll();G.updateGui()
    v.saveImage(str(ROOT/'previews/前侧.png'),1400,1100,'White')
    v.setCameraOrientation(A.Rotation(V(1,0,0),145).Q);v.fitAll();G.updateGui()
    v.saveImage(str(ROOT/'previews/后侧.png'),1400,1100,'White')
    v.viewAxonometric();v.fitAll()
    for tree in G.getMainWindow().findChildren(QtWidgets.QTreeWidget):
        tree.collapseAll()
        if tree.topLevelItemCount():tree.expandItem(tree.topLevelItem(0))
d.recompute()
import runpy
runpy.run_path(str(ROOT/'scripts/specifications.py'))['update'](d)
runpy.run_path(str(ROOT/'scripts/mount.py'))['build'](d)
d.Boss.Label='磁铁';d.BossSketch.Label='磁铁轮廓'
d.recompute();d.saveAs(str(ROOT/'models/HT2806.FCStd'))
if A.GuiUp:
    import runpy
    runpy.run_path(str(ROOT/'scripts/final_view.py'))
print('HT2806 BUILD OK',report)
