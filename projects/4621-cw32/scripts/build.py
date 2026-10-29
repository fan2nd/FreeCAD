"""Run with FreeCAD Python or exec from FreeCAD GUI. Preserves source history."""
from pathlib import Path
import math, json
import FreeCAD as A, Part, Sketcher, MeshPart
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'models/4621-cw32.FCStd'
SOURCE=OUT
for sub in ('models','print','previews','reports'):(ROOT/sub).mkdir(parents=True,exist_ok=True)
V=A.Vector

def build():
    d=A.openDocument(str(SOURCE)); d.Label='4621-cw32'
    d.Base.Tip=d.JointPattern
    for name in ['FixingPattern','FixingHole','FixingSketch']:
        if d.getObject(name):d.removeObject(name)
    d.BaseOutline.setDatum(8,A.Units.Quantity('-32 mm'))
    d.BaseOutline.setDatum(10,A.Units.Quantity('64 mm'))
    # Reuse the editable base history inside the sole project document.
    # Remove only script-owned downstream features before recreating them.
    board=d.getObject('Board')
    if board:
        names=[o.Name for o in reversed(board.Group)]
        names += [o.Name for o in board.Origin.OriginFeatures]+[board.Origin.Name,board.Name]
        for name in names:
            if d.getObject(name):d.removeObject(name)
    d.Upright.Tip=d.PilotPattern
    d.WireSketch.setExpression('Placement.Base.y',None)
    for name in ['WireMouthFillet','WireRamp','RampInner','RampOuter','Bevel','BevelEnd','BevelStart','BoardPocket','BoardHoles','SeatPad','SeatSketch','ReliefPocket','ReliefSketch','Notes','Params']:
        if d.getObject(name):d.removeObject(name)

    # Remove obsolete independent-encoder mounting features only in this new document.
    for name in ['EncoderMountPattern','EncoderMountHole','EncoderMountHoleSketch','EncoderSeatPocket','EncoderSeatSketch']:
        if d.getObject(name):d.removeObject(name)
    d.Upright.Tip=d.PilotPattern
    d.MotorHoleSketch.Placement.Rotation=A.Rotation(V(0,0,1),90)
    d.MotorPattern.Occurrences=2
    d.MotorPattern.Label='电机对角双孔'
    d.WireSketch.Placement.Rotation=A.Rotation(V(0,0,1),180)
    d.WireSketch.Placement.Base.y=2
    d.WireSketch.Label='上出线槽轮廓'
    d.WirePocket.Label='上出线槽'
    d.EncoderHole.Diameter=16.4
    d.EncoderSketch.setDatum(1,A.Units.Quantity('16.4 mm'))
    d.EncoderSketch.Label='中央孔轮廓'
    d.EncoderHole.Label='中央孔'
    d.recompute()
    p=d.addObject('Spreadsheet::Sheet','Params'); p.Label='安装参数'
    rows=[('磁铁凸出上限', 1, 'mm', 'MagnetMax'), ('封装表面最小间隙', '=BoardBack-SensorH-MagnetMax', 'mm', 'Gap'), ('编码器封装高度', 1.75, 'mm', 'SensorH'), ('板孔距', 19, 'mm', 'BoardPitch'), ('自攻导孔直径', 2.0, 'mm', 'BoardHole'), ('电机孔对角距', 38, 'mm', 'MotorPitch'), ('电机螺丝通孔', 3.4, 'mm', 'MotorHole'), ('板厚', 1.6, 'mm', 'BoardT'), ('板直径', 32, 'mm', 'BoardD'), ('接触台直径', 5.2, 'mm', 'SeatD'), ('径向间隙', 0.4, 'mm', 'RadialGap'), ('元件槽深', 3.5, 'mm', 'ReliefDepth'), ('螺丝头高', 1, 'mm', 'HeadH'), ('板背位置', '=StandBack-BoardT', 'mm', 'BoardBack'), ('立板背面位置', 6, 'mm', 'StandBack'), ('板安装角度', 135, 'deg', 'BoardAngle'), ('凸起直径', 16, 'mm', 'BossOD'), ('凸起径向余量', 0.2, 'mm', 'BossClearance'), ('斜面深度', '=BevelOuterR-BevelInnerR', 'mm', 'BevelDepth'), ('斜面入口半径', 8.2, 'mm', 'BevelOuterR'), ('斜面末端半径', 6.9, 'mm', 'BevelInnerR'), ('支柱角度', '=BoardAngle+90', 'deg', 'MountAngle'), ('缺口深度', 12, 'mm', 'NotchDepth'), ('螺丝头下长度', 6, 'mm', 'ScrewL')]
    for c,s in zip('ABCD',['参数','数值','单位','说明']): p.set(c+'1',s)
    for i,(label,val,unit,alias) in enumerate(rows,2):
        p.set('A'+str(i),label);p.set('B'+str(i),str(val));p.setAlias('B'+str(i),alias);p.set('C'+str(i),unit)
    p.set('D2','驱动新增安装特征；用户更新为小于1，按1作为保守上限；板正面与立板背面齐平')
    p.set('D3','无垫片，按磁铁凸出上限估算封装表面机械间隙')
    p.set('D4','常见SOIC8高度包络，需核对实际焊后高度')
    p.setColumnWidth('A',150);p.setColumnWidth('B',85);p.setColumnWidth('C',65);p.setColumnWidth('D',420)
    notes=d.addObject('Spreadsheet::Sheet','Notes');notes.Label='装配说明'
    texts=['底板64×55×6，长度与立板一致；外围四孔取消，仅保留两个立板连接沉孔。', '板固定两颗M2.5自攻、电机固定两颗M3，分别占两条垂直对角线，X字排布。', '独立新支架；原独立编码器四孔及方凹位取消，中央孔Ø16.4、无矩形支臂。', '选用较小的一对板孔，图纸Ø2.6，对应M2.5自攻；中心距19，支柱导孔暂定Ø2.0，按牙型和材料试配。', '两根Ø5.2支柱连接圆孔边缘；电机侧入口Ø16.4并以45度向内收小，无独立垫片。', '用户确认入口直径16.4，向内45度收小；深1.3后直径13.8，深入1 mm处直径14.4。此形状不提供Ø16直柱凸起的完整容纳空间。', 'A/B/C电机接口及电机线朝上，通过上沿14 mm宽、12 mm深直通缺口；取消走线斜坡，为U/V/W三个焊孔留出线空间；底部封平。CW32正面朝外。', 'PCB正面与立板背面齐平，板背位置4.4，SOP8包络暂按1.75；磁铁凸出小于1，封装表面机械间距约1.65–2.65 mm。', 'M2.5×6自攻，板厚1.6时进入塑料4.4，尖端恰好到电机贴合面，长度余量为0；板孔周需无元件。', '电机贴合面朝下打印；斜面45度，无螺母槽桥接，原底部横孔收口需切片核对。', '参考PCB不包含元件与接线包络，实际焊后高度、磁性能及自攻配合需试装验证。']
    for i,t in enumerate(texts,1):notes.set('A'+str(i),t)
    notes.setColumnWidth('A',850)
    d.WireSketch.setExpression('Placement.Base.y','23 - Params.NotchDepth - 13')
    b=d.Upright
    def sk(name,label,z=None):
        s=d.addObject('Sketcher::SketchObject',name);b.addObject(s);s.Label=label
        if z:s.setExpression('Placement.Base.z',z)
        return s
    def circ(s,x,y,r,xe=None,ye=None,re=None):
        k=s.addGeometry(Part.Circle(V(x,y,0),V(0,0,1),r),False)
        for kind,val,expr in [('DistanceX',x,xe),('DistanceY',y,ye)]:
            if val==0 and not expr:s.addConstraint(Sketcher.Constraint(kind,k,3,0.0))
            else:
                j=s.addConstraint(Sketcher.Constraint(kind,k,3,val))
                if expr:s.setExpression('Constraints[%d]'%j,expr)
        j=s.addConstraint(Sketcher.Constraint('Radius',k,r))
        if re:s.setExpression('Constraints[%d]'%j,re)
    def poly(s,pts,exprs=None):
        for i,(x,y) in enumerate(pts):
            j=(i+1)%len(pts);xx,yy=pts[j]
            k=s.addGeometry(Part.LineSegment(V(x,y,0),V(xx,yy,0)),False)
            for point,index,values in [(1,i,(x,y)),(2,j,(xx,yy))]:
                for axis,(kind,val) in enumerate(zip(['DistanceX','DistanceY'],values)):
                    c=s.addConstraint(Sketcher.Constraint(kind,k,point,val))
                    if exprs:s.setExpression('Constraints[%d]'%c,exprs[index][axis])
    def feat(s,name,label,typ,length,rev=False):
        f=b.newObject('PartDesign::'+typ,name);f.Label=label;f.Profile=s;f.setExpression('Length',length);f.Reversed=rev;f.Refine=True;d.recompute();s.Visibility=False
        for o in b.Group:
            if hasattr(o,'Shape') and o!=f:o.Visibility=False
        if f.Shape.isNull():
            print('FAILED',name,f.State,f.getStatusString(),s.SolverMessages if hasattr(s,'SolverMessages') else '', flush=True)
            raise RuntimeError(name)
        return f
    def rect(s,x0,x1,half,ex0,ex1,eh):
        poly(s,[(x0,-half),(x1,-half),(x1,half),(x0,half)],[(ex0,'-('+eh+')'),(ex1,'-('+eh+')'),(ex1,eh),(ex0,eh)])
    s=sk('ReliefSketch','元件槽轮廓');circ(s,0,0,16.4,re='Params.BoardD / 2 + Params.RadialGap')
    f=feat(s,'ReliefPocket','元件槽','Pocket','Params.ReliefDepth',True)
    front='Params.StandBack'
    top='Params.StandBack - Params.BoardBack'
    s=sk('SeatSketch','支柱轮廓',front)
    for sign in [-1,1]:circ(s,sign*9.5,0,2.6,xe=f'{sign} * Params.BoardPitch / 2',re='Params.SeatD / 2')
    s.Placement.Rotation=A.Rotation(V(0,0,1),225)
    s.setExpression('Placement.Rotation.Angle','Params.MountAngle')
    f=feat(s,'SeatPad','支柱','Pad','Params.BoardBack',True)
    s=sk('BoardHoles','板孔位',top)
    for sign in [-1,1]:circ(s,sign*9.5,0,1.0,xe=f'{sign} * Params.BoardPitch / 2',re='Params.BoardHole / 2')
    s.Placement.Rotation=A.Rotation(V(0,0,1),225)
    s.setExpression('Placement.Rotation.Angle','Params.MountAngle')
    f=feat(s,'BoardPocket','板螺丝孔','Pocket','Params.BoardBack',True)
    s0=sk('BevelStart','斜面入口',front)
    circ(s0,0,0,8.2,re='Params.BevelOuterR')
    s1=sk('BevelEnd','斜面末端',front+' - Params.BevelDepth')
    circ(s1,0,0,6.9,re='Params.BevelInnerR')
    f=b.newObject('PartDesign::SubtractiveLoft','Bevel');f.Label='柱底斜面'
    f.Profile=s0;f.Sections=[s1];f.Ruled=True;f.Refine=True
    d.recompute();s0.Visibility=False;s1.Visibility=False;d.BoardPocket.Visibility=False
    # Round only the two corners where the open slot meets the R23 outer arc.
    previous=b.Tip
    localshape=b.Shape.copy();localshape.Placement=b.Placement.inverse().multiply(localshape.Placement)
    mouth=[]
    for i,edge in enumerate(localshape.Edges,1):
        bb=edge.BoundBox
        if bb.XLength<1e-6 and bb.YLength<1e-6 and abs(abs(bb.XMin)-7)<1e-6 and abs(bb.YMin-math.sqrt(23**2-7**2))<1e-6 and bb.ZLength>5.99:
            mouth.append('Edge'+str(i))
    assert len(mouth)==2,mouth
    f=b.newObject('PartDesign::Fillet','WireMouthFillet');f.Label='缺口口角圆角'
    f.Base=(previous,mouth);f.Radius=2;d.recompute();previous.Visibility=False
    assert not f.Shape.isNull() and f.Shape.isValid() and len(f.Shape.Solids)==1
    # Editable board envelope, hidden by default; no invented component models.
    ref=d.addObject('PartDesign::Body','Board');ref.Label='驱动板'
    ref.Placement=b.Placement
    ref.setExpression('Placement', 'Upright.Placement')
    ref.addProperty('App::PropertyString','MotorLeads','安装').MotorLeads='A/B/C 朝上，走立板上沿缺口；CW32正面朝外'
    s=d.addObject('Sketcher::SketchObject','PCBOutline');ref.addObject(s);s.Label='板轮廓';s.setExpression('Placement.Base.z','Params.StandBack - Params.BoardBack')
    circ(s,0,0,16,re='Params.BoardD / 2')
    pad=ref.newObject('PartDesign::Pad','PCBPad');pad.Label='板厚';pad.Profile=s;pad.setExpression('Length','Params.BoardT');pad.Reversed=True;d.recompute();s.Visibility=False
    s=d.addObject('Sketcher::SketchObject','PCBMount');ref.addObject(s);s.Label='板安装孔';s.setExpression('Placement.Base.z','Params.StandBack - Params.BoardBack - Params.BoardT')
    for x,y,r in [(-9.5,0,1.5),(9.5,0,1.5),(0,9.5,1.3),(0,-9.5,1.3)]:circ(s,x,y,r)
    s.Placement.Rotation=A.Rotation(V(0,0,1),135)
    s.setExpression('Placement.Rotation.Angle','Params.BoardAngle')
    cut=ref.newObject('PartDesign::Pocket','PCBDrill');cut.Label='板孔';cut.Profile=s;cut.setExpression('Length','Params.BoardT');cut.Reversed=True;d.recompute();s.Visibility=False;pad.Visibility=False
    d.Upright.Label='立板';d.Base.Label='底板'
    for body in [d.Upright,d.Base,ref]:
        for o in body.Group:
            if hasattr(o,'ViewObject'):o.Visibility=False
        body.Visibility=True;body.Tip.Visibility=True
    ref.Visibility=False
    if A.GuiUp:
        b.ViewObject.ShapeColor=(0.9,0.55,0.16);f.ViewObject.ShapeColor=(0.9,0.55,0.16)
        ref.ViewObject.ShapeColor=(0.12,0.5,0.22);cut.ViewObject.ShapeColor=(0.12,0.5,0.22)
    d.recompute()
    report={}
    for body in [d.Upright,d.Base,ref]:
        report[body.Name]={'valid':body.Shape.isValid(),'solids':len(body.Shape.Solids),'volume':body.Shape.Volume}
        assert body.Shape.isValid() and len(body.Shape.Solids)==1,body.Name
    for other in [d.Base,ref]:
        overlap=b.Shape.common(other.Shape).Volume;report['overlap_'+other.Name]=overlap;assert overlap<1e-7
    # Confirm the new diagonal arms did not fill original motor screw bores.
    shape=b.Shape.copy();shape.Placement=b.Placement.inverse().multiply(shape.Placement)
    motor_points=[(-13.435,13.435),(13.435,-13.435)]
    for x,y in motor_points:
        assert shape.common(Part.makeCylinder(1.60,6,V(x,y,0))).Volume<1e-7
    for x,y in [(-13.435,-13.435),(13.435,13.435)]:
        assert shape.isInside(V(x,y,4.5),1e-6,True), 'Unused motor hole remains'
    axis=d.SeatSketch.Placement.Rotation.multVec(V(1,0,0))
    assert abs(axis.dot(V(1,-1,0)))<1e-6, 'Mounting axes are not perpendicular'
    report['motor_screws']=2;report['board_screws']=2;report['mounting_layout']='X; perpendicular diagonal pairs'
    bevel_tool=Part.makeCone(float(p.BevelOuterR),float(p.BevelInnerR),float(p.BevelDepth),V(0,0,6),V(0,0,-1))
    assert shape.common(bevel_tool).Volume<1e-7
    assert abs((float(p.BevelOuterR)-float(p.BevelInnerR))/float(p.BevelDepth)-1)<1e-8
    report['bevel_entry_diameter_mm']=16.4
    report['bevel_angle_deg']=45
    report['bevel_depth_mm']=1.3
    # User explicitly chose the taper entrance diameter, not cylindrical boss clearance.
    boss=Part.makeCylinder(8,1,V(0,0,6),V(0,0,-1))
    report['nominal_16x1_boss_interference_mm3']=shape.common(boss).Volume
    report['center_cut_diameter_mm']=float(d.EncoderHole.Diameter)
    report['support_arms_removed']=d.getObject('ArmPad') is None
    report['motor_bores_clear']=True
    assert shape.isInside(V(0,-20,3),1e-6,True), 'Bottom notch remains'
    assert not shape.isInside(V(0,20,3),1e-6,True), 'Top notch blocked'
    report['wire_notch']='top; bottom filled'
    report['notch_depth_mm']=12
    report['wire_mouth_fillet_mm']=2
    report['wire_mouth_corners']=2
    report['wire_ramp_removed']=d.getObject('WireRamp') is None
    assert shape.isInside(V(0,10.9,5.99),1e-6,True)
    assert not shape.isInside(V(0,11.1,5.99),1e-6,True)
    # Conservative routing window, not a measured PCB component model.
    window=Part.makeBox(10,12,6,V(-5,13,0))
    assert shape.common(window).Volume<1e-7
    report['routing_window_mm']={'width':10,'bottom_from_center':13,'through_thickness':6}
    report['legacy_encoder_features_removed']=not any(d.getObject(n) for n in ['EncoderMountPattern','EncoderSeatPocket'])
    report['board_angle_deg']=135
    report['pilot_diameter_mm']=float(p.BoardHole)
    report['motor_terminal_direction']='up through upper notch'
    # Actual model motor-hole pitch is rounded to 13.435 per coordinate: clearance covers <0.001 mm discrepancy.
    report['motor_alignment_error_mm']=abs(19/math.sqrt(2)-13.435)*math.sqrt(2)
    for left,right in [(d.Upright,ref),(d.Base,ref)]:
        overlap=left.Shape.common(right.Shape).Volume;report['overlap_'+left.Name+'_Board']=overlap;assert overlap<1e-7
    cell='B'+str(next(i for i,row in enumerate(rows,2) if row[3]=='BoardT'))
    old=b.Shape.Volume;p.set(cell,'1.8');d.recompute();assert b.Shape.isValid() and b.Shape.Volume<old
    assert abs(float(p.BoardBack)+float(p.BoardT)-float(p.StandBack))<1e-8
    p.set(cell,'1.6');d.recompute();report['flush_recompute']=True
    report['pcb_front_mm']=float(p.BoardBack)+float(p.BoardT)
    report['screw_length_mm']=float(p.ScrewL)
    report['screw_tip_clearance_mm']=float(p.BoardBack)+float(p.BoardT)-float(p.ScrewL)
    assert abs(report['pcb_front_mm']-float(p.StandBack))<1e-8
    report.update(board_back_mm=float(p.BoardBack),sensor_surface_mm=float(p.BoardBack)-float(p.SensorH),magnet_protrusion_range_mm=[0,1],package_surface_gap_range_mm=[1.65,2.65],selected_board_hole_mm=2.6,screw_nominal_mm=2.5,component_relief_mm=1.9)
    assert not [o.Name for o in d.Objects if 'Invalid' in o.State]
    Part.export([d.Upright,d.Base],str(ROOT/'models/4621-cw32.step'))
    Part.export([d.Upright],str(ROOT/'models/立板.step'))
    Part.export([d.Base],str(ROOT/'models/底板.step'))
    MeshPart.meshFromShape(Shape=d.Base.Shape,LinearDeflection=0.08,AngularDeflection=0.15,Relative=False).write(str(ROOT/'print/底板.stl'))
    assert abs(d.Base.Shape.BoundBox.XLength-64)<1e-8
    assert d.Base.Tip==d.JointPattern
    report['base_size_mm']=[64,55,6]
    report['base_perimeter_holes_removed']=True
    local=b.Shape.copy();local.Placement=b.Placement.inverse().multiply(local.Placement)
    local.rotate(V(0,0,0),V(1,0,0),180);local.translate(V(0,0,6))
    mesh=MeshPart.meshFromShape(Shape=local,LinearDeflection=0.08,AngularDeflection=0.15,Relative=False)
    mesh.write(str(ROOT/'print/立板.stl'));report['print_bounds']=str(mesh.BoundBox)
    overhangs=[];previous=None
    for i in range(30):
        z=(i+0.37)*0.2
        face=Part.makeFace(local.slice(V(0,0,1),z),'Part::FaceMakerBullseye');face.translate(V(0,0,-z))
        if previous is not None:
            extra=face.cut(previous)
            if extra.Area>0.01:overhangs.append({'z':round(z,2),'area':extra.Area,'regions':[[round(f.BoundBox.XLength,3),round(f.BoundBox.YLength,3)] for f in extra.Faces]})
        previous=face
    report['print_layer_expansions']=overhangs
    (ROOT/'reports/integral_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    d.recompute();d.saveAs(str(OUT))
    if A.GuiUp:
        import FreeCADGui as G
        G.Selection.clearSelection();G.activeDocument().activeView().viewAxonometric();G.activeDocument().activeView().fitAll();d.save()
        import runpy
        runpy.run_path(str(ROOT/'scripts/final_view.py'))
    return d

if __name__=='__main__':build()
