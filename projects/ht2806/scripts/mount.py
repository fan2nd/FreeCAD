"""Native CW32 support history, built in the motor's document."""
from pathlib import Path
import math,json
import FreeCAD as A, Part, Sketcher, MeshPart
ROOT=Path(__file__).resolve().parents[1]
V=A.Vector

def build(d):
    p=d.addObject('Spreadsheet::Sheet','MountParams');p.Label='支架参数'
    rows=[('立板厚',6,'Wall','mm'),('板厚',1.6,'BoardT','mm'),('封装高',1.75,'SensorH','mm'),('磁铁高度','=Params.BossH','MagnetH','mm'),('板背位置','=Wall+BoardLift','BoardBack','mm'),('封装表面间隙','=BoardBack-SensorH-MagnetH','Gap','mm'),('支柱根径',5.2,'RootD','mm'),('支柱顶径',4,'TipD','mm'),('板孔距',19,'Pitch','mm'),('自攻导孔',2,'PilotD','mm'),('板底架空高',0.6,'BoardLift','mm'),('元件高度包络',1.75,'ComponentH','mm'),('元件槽深',1.6,'RecessDepth','mm'),('元件槽径',32.6,'RecessD','mm'),('螺丝沉孔深','=Wall-(MotorScrewL-MotorEngage)','CounterDepth','mm'),('螺丝沉孔径',4.2,'CounterD','mm'),('电机螺丝总长',6,'MotorScrewL','mm'),('旋入电机深度',2,'MotorEngage','mm'),('电机螺丝头径',3.7,'MotorHeadD','mm'),('商家头部厚度',1.7,'MotorHeadH','mm'),('沉头角度',90,'HeadAngle','deg'),('沉头锥段深','= (MotorHeadD-2)/2','HeadConeH','mm'),('锥座深','= (MotorHeadD-MotorHole)/2','SeatConeH','mm'),('中央孔径','=Params.BossD+1','CenterD','mm'),('电机通孔',2.2,'MotorHole','mm'),('缺口宽',8,'NotchW','mm'),('缺口深',8.8,'NotchDepth','mm'),('缺口口角',2,'MouthR','mm'),('板螺丝头下长',6,'ScrewL','mm'),('板孔安装角',225,'Angle','deg'),('打印层高',0.2,'LayerH','mm'),('底板沉孔深',2.6,'BaseCounterDepth','mm')]
    for c,t in zip('ABCD',['参数','数值','单位','说明']):p.set(c+'1',t)
    for i,(title,value,alias,unit) in enumerate(rows,2):
        for c,val in [('A',title),('B',str(value)),('C',unit)]:p.set(c+str(i),val)
        p.setAlias('B'+str(i),alias)
    p.set('D2','驱动支架功能尺寸；底板46×40×5，顶部外圆R17.3；整体紧凑化，功能孔位不缩放')
    p.set('D4','沿用SOP8封装高假设，实际焊后高度待测')
    p.set('D5','用户确认原图Ø12×3凸台就是磁铁')

    for alias in ['NotchW','NotchDepth','MouthR','ScrewL','MotorHeadH','HeadAngle','LayerH']:
        i=next(i for i,row in enumerate(rows,2) if row[2]==alias);p.set('D'+str(i),'记录值；对应草图/圆角尺寸在原生特征中编辑' if alias!='ScrewL' else '选用螺丝长度；用于余量校验')
    p.setColumnWidth('A',155);p.setColumnWidth('D',450)
    n=d.addObject('Spreadsheet::Sheet','MountNotes');n.Label='支架说明'
    notes=['CW32沿用同一驱动板；两颗M2.5×6自攻，Ø2.0导孔；根部Ø5.2至顶端Ø4锥形支柱，露出立板背面高0.6 mm。','电机用后面16×20.5矩形孔中的对角两颗M2，电机出线转到上方。板柱占另一对角方向；两条轴不严格垂直。','用户确认Ø12×3凸台为磁铁；按直圆柱避让，中央Ø13贯通，不沿用4621向内收口。','立板厚6 mm，板底元件槽Ø32.6深1.6，保留两柱根；板底架空0.6 mm，板背6.6、SOP8表面4.85，相对3 mm磁铁名义间隙1.85；按底面元件高1.75留0.45 mm余量。','PCB两颗M2.5×6自攻进入塑料4.4，距电机贴合面2.2 mm。电机固定按用户指定M2×6沉头内梅花螺丝，总长含头部6 mm，头顶距电机面4 mm，进入电机2 mm。','电机沉头Ø3.7、总长6、T6；商家头部厚1.7仅记录，锥角按用户接受的90°假设，Ø3.7至Ø2锥段深0.85。螺丝头顶距PCB底面2.6 mm；立板外侧Ø4.2入口孔深2，下接90°锥座至Ø2.2，锥座深0.75。实际锥角和就位深度需试装，参考不生成牙型或内梅花','上缺口宽8、深8.8、底角R2、与外圆相接口角R2，为电机线和板UVW预留上出口，名义8 mm宽，槽底在中心上方8.5，与磁铁孔保留2 mm连接壁；通道覆盖背面出线方块上部，7.8 mm净宽校验从中心上方12.5起；方块用途已由用户确认，尺寸仍为原图比例估算。','底板46×40×5，仅两颗立板连接螺丝；立板电机面朝下打印，底板底面朝下。打印层高及首层0.2 mm；立板背面6、槽底4.4、柱顶6.6、自攻孔底2.2均为整层；底板厚5、底面沉孔深2.6。沉头锥面按功能角度保留。','PCB参考没有真实元件；磁性能、自攻强度及实际元件间隙需实物验证。']
    for i,t in enumerate(notes,1):n.set('A'+str(i),t)
    n.setColumnWidth('A',900);d.recompute()
    def sketch(body,name,z=0):
        s=body.newObject('Sketcher::SketchObject',name)
        if isinstance(z,str):s.setExpression('Placement.Base.z',z)
        else:s.Placement.Base.z=z
        return s
    def circle(s,x,y,r,xe=None,ye=None,re=None):
        k=s.addGeometry(Part.Circle(V(x,y,0),V(0,0,1),r),False)
        for kind,val,expr in [('DistanceX',x,xe),('DistanceY',y,ye),('Radius',r,re)]:
            c=s.addConstraint(Sketcher.Constraint(kind,k,val) if kind=='Radius' else Sketcher.Constraint(kind,k,3,val))
            if expr:s.setExpression('Constraints[%d]'%c,expr)
    def fixed(s,geos):
        for g in geos:
            i=s.addGeometry(g,False);s.addConstraint(Sketcher.Constraint('Block',i))
    def poly(s,pts):fixed(s,[Part.LineSegment(V(*a,0),V(*b,0)) for a,b in zip(pts,pts[1:]+pts[:1])])
    def feature(body,s,name,typ,length,rev=False):
        f=body.newObject('PartDesign::'+typ,name);f.Profile=s;f.Reversed=rev;f.Refine=True
        if isinstance(length,str):f.setExpression('Length',length)
        else:f.Length=length
        d.recompute();assert not f.Shape.isNull() and f.Shape.isValid(),(name,f.getStatusString())
        for o in body.Group:o.Visibility=False
        f.Visibility=True;return f
    def fillet(body,previous,name,edges,r):
        f=body.newObject('PartDesign::Fillet',name);f.Base=(previous,edges);f.Radius=r;d.recompute()
        assert not f.Shape.isNull() and f.Shape.isValid(),name
        previous.Visibility=False;return f
    b=d.addObject('PartDesign::Body','Upright');b.Label='立板'
    b.Placement=A.Placement(V(0,6,27),A.Rotation(V(1,0,0),90));b.setExpression('Placement.Base.y','MountParams.Wall')
    s=sketch(b,'StandOutline');s.Label='立板轮廓'
    # Tangency point between R17.3 and the lines from (+/-23,-17).
    q=V(23,-17,0);q2=q.dot(q);r=17.3
    t=q*(r*r/q2)+V(-q.y,q.x,0)*(r*math.sqrt(q2-r*r)/q2)
    pts=[V(-23,-22,0),V(23,-22,0),V(23,-17,0),t]
    fixed(s,[Part.LineSegment(pts[i],pts[i+1]) for i in range(3)]+[Part.Arc(t,V(0,17.3,0),V(-t.x,t.y,0)),Part.LineSegment(V(-t.x,t.y,0),V(-23,-17,0)),Part.LineSegment(V(-23,-17,0),pts[0])])
    f=feature(b,s,'StandPad','Pad','MountParams.Wall');f.Label='立板拉伸'
    edges=['Edge'+str(i) for i,e in enumerate(f.Shape.Edges,1) if e.BoundBox.ZLength>float(p.Wall)-0.01 and abs(abs(e.CenterOfMass.x)-23)<1e-6 and abs(e.CenterOfMass.y+17)<1e-6]
    f=fillet(b,f,'FootRound',edges,8);f.Label='底脚圆角'
    s=sketch(b,'CenterOpening');s.Label='磁铁避让轮廓';circle(s,0,0,6.5,re='MountParams.CenterD/2')
    f=feature(b,s,'CenterPocket','Pocket','MountParams.Wall',True);f.Label='磁铁避让'
    # Fixed outline dimensions are recorded separately from driven functional dimensions.
    s=sketch(b,'TopWireOutline');s.Label='出线轮廓'
    w=4;floor=8.5;rr=2
    fixed(s,[Part.LineSegment(V(-w,30,0),V(-w,floor+rr,0)),Part.Arc(V(-w,floor+rr,0),V(-w+rr-rr/math.sqrt(2),floor+rr-rr/math.sqrt(2),0),V(-w+rr,floor,0)),Part.LineSegment(V(-w+rr,floor,0),V(w-rr,floor,0)),Part.Arc(V(w-rr,floor,0),V(w-rr+rr/math.sqrt(2),floor+rr-rr/math.sqrt(2),0),V(w,floor+rr,0)),Part.LineSegment(V(w,floor+rr,0),V(w,30,0)),Part.LineSegment(V(w,30,0),V(-w,30,0))])
    f=feature(b,s,'TopWirePocket','Pocket','MountParams.Wall',True);f.Label='上出线槽'
    edges=['Edge'+str(i) for i,e in enumerate(f.Shape.Edges,1) if e.BoundBox.ZLength>float(p.Wall)-0.01 and e.BoundBox.XLength<1e-6 and e.BoundBox.YLength<1e-6 and abs(abs(e.CenterOfMass.x)-w)<1e-6 and abs(e.CenterOfMass.y-math.sqrt(17.3**2-w**2))<1e-6]
    assert len(edges)==2,edges
    f=fillet(b,f,'WireMouthFillet',edges,2);f.Label='缺口口角圆角'
    s=sketch(b,'ComponentOutline');s.Label='元件避让轮廓'
    circle(s,0,0,16.3,re='MountParams.RecessD/2')
    for sign in [-1,1]:
        c=sign*9.5/math.sqrt(2)
        circle(s,c,c,2.6,xe=f'{sign}*MountParams.Pitch/2/sqrt(2)',ye=f'{sign}*MountParams.Pitch/2/sqrt(2)',re='MountParams.RootD/2')
    f=feature(b,s,'ComponentPocket','Pocket','MountParams.RecessDepth',True);f.Label='元件避让槽'
    # Magnet-facing root to PCB-facing tip; two separate native lofts.
    for sign,suffix in [(-1,''),(1,'2')]:
        previous=b.Tip
        a=sketch(b,'PostRoot'+suffix);a.Label='柱根轮廓'+suffix
        z=sketch(b,'PostTip'+suffix,'MountParams.Wall-MountParams.BoardBack');z.Label='柱顶轮廓'+suffix
        for skt,diam in [(a,'RootD'),(z,'TipD')]:
            circle(skt,sign*9.5,0,2,xe=f'{sign}*MountParams.Pitch/2',re='MountParams.'+diam+'/2')
            skt.Placement.Rotation=A.Rotation(V(0,0,1),225);skt.setExpression('Placement.Rotation.Angle','MountParams.Angle')
        f=b.newObject('PartDesign::AdditiveLoft','PostLoft'+suffix);f.Label='锥形支柱'+suffix;f.Profile=a;f.Sections=[z];f.Ruled=True;f.Refine=True;d.recompute()
        assert f.Shape.isValid() and len(f.Shape.Solids)==1
        a.Visibility=False;z.Visibility=False;previous.Visibility=False
    s=sketch(b,'BoardPilotOutline','MountParams.Wall-MountParams.BoardBack');s.Label='板螺丝孔位'
    for sign in [-1,1]:circle(s,sign*9.5,0,1,xe=f'{sign}*MountParams.Pitch/2',re='MountParams.PilotD/2')
    s.Placement.Rotation=A.Rotation(V(0,0,1),225);s.setExpression('Placement.Rotation.Angle','MountParams.Angle')
    f=feature(b,s,'BoardPilotPocket','Pocket','MountParams.ScrewL-MountParams.BoardT',True);f.Label='板自攻底孔'
    s=sketch(b,'MotorMountOutline');s.Label='电机双孔位'
    for sign in [-1,1]:circle(s,sign*10.25,-sign*8,1.1,xe=f'{sign}*Params.RearY/2',ye=f'{-sign}*Params.RearX/2',re='MountParams.MotorHole/2')
    f=feature(b,s,'MotorMountPocket','Pocket','MountParams.Wall',True);f.Label='电机双孔'
    s=sketch(b,'MotorCounterOutline');s.Label='电机沉孔轮廓'
    for sign in [-1,1]:circle(s,sign*10.25,-sign*8,2.1,xe=f'{sign}*Params.RearY/2',ye=f'{-sign}*Params.RearX/2',re='MountParams.CounterD/2')
    f=feature(b,s,'MotorCounterPocket','Pocket','MountParams.CounterDepth',True);f.Label='电机螺丝沉孔'
    for i,sign in enumerate([1,-1],1):
        previous=b.Tip
        top=sketch(b,'SeatConeTop'+str(i),'MountParams.CounterDepth');top.Label='锥座入口'
        end=sketch(b,'SeatConeEnd'+str(i),'MountParams.CounterDepth+MountParams.SeatConeH');end.Label='锥座末端'
        for skt,diam in [(top,'MotorHeadD'),(end,'MotorHole')]:
            circle(skt,sign*10.25,-sign*8,1.5,xe=f'{sign}*Params.RearY/2',ye=f'{-sign}*Params.RearX/2',re='MountParams.'+diam+'/2')
        f=b.newObject('PartDesign::SubtractiveLoft','SeatCone'+str(i));f.Label='沉头锥座'+str(i);f.Profile=top;f.Sections=[end];f.Ruled=True;f.Refine=True
        d.recompute();assert f.Shape.isValid() and len(f.Shape.Solids)==1
        top.Visibility=False;end.Visibility=False;previous.Visibility=False
    s=sketch(b,'StandJointOutline');s.Label='底脚螺丝孔位';s.Placement=A.Placement(V(0,-22,3.5),A.Rotation(V(1,0,0),90));s.setExpression('Placement.Base.z','MountParams.Wall/2')
    for x in [-14,14]:circle(s,x,0,1.25)
    f=feature(b,s,'StandJointPocket','Pocket',5.2);f.Label='底脚螺丝孔'
    base=d.addObject('PartDesign::Body','Base');base.Label='底板'
    s=sketch(base,'BaseOutline');s.Label='底板轮廓';poly(s,[(-23,-25),(23,-25),(23,15),(-23,15)])
    f=feature(base,s,'BasePad','Pad',5);f.Label='底板拉伸'
    edges=['Edge'+str(i) for i,e in enumerate(f.Shape.Edges,1) if e.BoundBox.ZLength>4.99]
    f=fillet(base,f,'BaseRound',edges,4);f.Label='底板圆角'
    for name,rad,depth in [('BaseJoint',1.65,5),('BaseCounter',2.75,'MountParams.BaseCounterDepth')]:
        s=sketch(base,name+'Outline');s.Label='连接孔位'
        for x in [-14,14]:circle(s,x,3.5,rad,ye='MountParams.Wall/2')
        f=feature(base,s,name+'Pocket','Pocket',depth,True);f.Label='连接通孔' if rad<2 else '连接沉孔'
    board=d.addObject('PartDesign::Body','Board');board.Label='驱动板';board.setExpression('Placement','Upright.Placement')
    s=sketch(board,'PCBOutline','MountParams.Wall-MountParams.BoardBack-MountParams.BoardT');s.Label='板轮廓';circle(s,0,0,16)
    f=feature(board,s,'PCBPad','Pad','MountParams.BoardT');f.Label='板厚'
    s=sketch(board,'PCBMountOutline','MountParams.Wall-MountParams.BoardBack-MountParams.BoardT');s.Label='板孔位'
    for x,y,r in [(-9.5,0,1.5),(9.5,0,1.5),(0,-9.5,1.3),(0,9.5,1.3)]:circle(s,x,y,r)
    s.Placement.Rotation=A.Rotation(V(0,0,1),135)
    f=feature(board,s,'PCBMountPocket','Pocket','MountParams.BoardT',True);f.Label='板安装孔'
    # Rear motor X points down, Y right, Z toward the front of the assembly.
    d.Motor.Placement=A.Placement(V(0,0,27),A.Rotation(V(0,0,-1),V(1,0,0),V(0,-1,0),'ZXY'))
    d.recompute()
    report={}
    levels={'wall':float(p.Wall),'recess_floor':float(p.Wall)-float(p.RecessDepth),'post_top':float(p.BoardBack),'pcb_pilot_bottom':float(p.BoardBack)+float(p.BoardT)-float(p.ScrewL),'motor_head_seat':float(p.MotorScrewL)-float(p.MotorEngage),'base_top':5.,'base_counter_floor':float(p.BaseCounterDepth)}
    for name,height in levels.items():
        assert abs(height/float(p.LayerH)-round(height/float(p.LayerH)))<1e-7,(name,height)
    report['print_layer_mm']=float(p.LayerH);report['print_plane_heights_mm']=levels
    for body in [b,base,board,d.Motor]:
        assert body.Shape.isValid() and len(body.Shape.Solids)==1,body.Name
        report[body.Name]={'volume':body.Shape.Volume,'valid':True}
        for o in body.Group:o.Visibility=False
        body.Visibility=True;body.Tip.Visibility=True
    for one,two in [(b,base),(b,board),(b,d.Motor),(board,d.Motor),(base,d.Motor)]:
        v=one.Shape.common(two.Shape).Volume;report[one.Name+'_'+two.Name]=v;assert v<1e-7,(one.Name,two.Name,v)
    # Check clearance of the real cylindrical magnet and the assumed SOP8 envelope.
    sensor=Part.makeBox(5,1.75,6,V(-2.5,float(p.BoardBack)-float(p.SensorH),24))
    assert sensor.common(d.Motor.Shape).Volume<1e-7
    assert sensor.common(b.Shape).Volume<1e-7
    window=Part.makeBox(7.8,float(p.Wall),10,V(-3.9,0,39.5))
    assert window.common(b.Shape).Volume<1e-7
    # The magnetic bore stays closed on the motor-facing wall, 2 mm below the slot.
    local=b.Shape.copy();local.Placement=b.Placement.inverse().multiply(local.Placement)
    bridge=Part.makeBox(1,1.9,float(p.Wall)-float(p.RecessDepth)-.2,V(-.5,6.55,float(p.RecessDepth)+.1))
    assert abs(local.common(bridge).Volume-bridge.Volume)<1e-7
    assert local.common(Part.makeCylinder(6.5,float(p.Wall),V(0,0,0))).Volume<1e-7
    report['magnet_bore_closed']=True;report['bridge_height_mm']=2
    report['wire_window_above_axis_mm']=12.5
    for x,z in [(10.25,19),(-10.25,35)]:
        shaft=Part.makeCylinder(1,6,V(x,4,z),V(0,-1,0))
        head=Part.makeCone(1.85,1,.85,V(x,4,z),V(0,-1,0))
        assert shaft.common(b.Shape).Volume<1e-7 and shaft.common(d.Motor.Shape).Volume<1e-7
        assert head.common(b.Shape).Volume<1e-7 and head.common(board.Shape).Volume<1e-7
    report['motor_screw_type']='M2x6 countersunk; 6 mm includes head; 90 degree assumed'
    report['motor_screw_head_diameter_mm']=3.7
    report['seat_cone_depth_mm']=.75
    report['motor_screw_engagement_mm']=2
    report['motor_screw_head_to_pcb_mm']=float(p.BoardBack)-4
    assert report['motor_screw_head_to_pcb_mm']>=2.5-1e-7
    report.update(center_opening_mm=float(p.CenterD),wire_notch_width_mm=float(p.NotchW),magnet_diameter_mm=12,magnet_height_mm=3,package_surface_gap_mm=float(p.Gap),pcb_screw_end_clearance_mm=float(p.BoardBack)+float(p.BoardT)-float(p.ScrewL),component_collision_verified=False)
    # Uniform underside envelope, excluding the necessary mounting-post contact areas.
    components=Part.makeCylinder(16,float(p.ComponentH),V(0,float(p.BoardBack)-float(p.ComponentH),27),V(0,1,0))
    for sign in [-1,1]:
        c=sign*9.5/math.sqrt(2)
        components=components.cut(Part.makeCylinder(2.7,float(p.ComponentH),V(c,float(p.BoardBack)-float(p.ComponentH),27+c),V(0,1,0)))
    assert components.common(b.Shape).Volume<1e-7
    for x,z in [(10.25,19),(-10.25,35)]:assert components.common(Part.makeCone(1.85,1,.85,V(x,4,z),V(0,-1,0))).Volume<1e-7
    report['component_envelope_height_mm']=float(p.ComponentH)
    report['component_envelope_clearance_mm']=float(p.BoardLift)+float(p.RecessDepth)-float(p.ComponentH)
    assert report['component_envelope_clearance_mm']>=.25-1e-7
    report['board_lift_mm']=float(p.BoardLift)
    report['component_recess_depth_mm']=float(p.RecessDepth)
    report['component_recess_removed']=d.getObject('ComponentPocket') is None
    # Functional parameters drive geometry and survive recomputation.
    cell='B'+str(next(i for i,row in enumerate(rows,2) if row[2]=='TipD'))
    before=b.Shape.Volume;p.set(cell,'4.2');d.recompute();assert b.Shape.isValid() and b.Shape.Volume>before
    p.set(cell,'4');d.recompute();assert abs(b.Shape.Volume-before)<1e-6
    assert not [o.Name for o in d.Objects if 'Invalid' in o.State]
    (ROOT/'print').mkdir(exist_ok=True)
    for body,name in [(b,'立板'),(base,'底板')]:
        Part.export([body],str(ROOT/'models'/(name+'.step')))
        shape=body.Shape.copy()
        if body==b:
            shape.Placement=body.Placement.inverse().multiply(shape.Placement);shape.rotate(V(),V(1,0,0),180);shape.translate(V(0,0,float(p.Wall)))
        MeshPart.meshFromShape(Shape=shape,LinearDeflection=.06,AngularDeflection=.12,Relative=False).write(str(ROOT/'print'/(name+'.stl')))
    screws=[]
    for i,sign in enumerate([1,-1],1):
        screw=d.addObject('PartDesign::Body','MotorScrew'+str(i));screw.Label='电机螺丝'+str(i)
        screw.Placement=A.Placement(V(sign*10.25,4,27-sign*8),A.Rotation(V(1,0,0),-90))
        screw.setExpression('Placement.Base.x',f'{sign}*Params.RearY/2')
        screw.setExpression('Placement.Base.z',f'27-{sign}*Params.RearX/2')
        screw.setExpression('Placement.Base.y','MountParams.MotorScrewL-MountParams.MotorEngage')
        sc=sketch(screw,'MotorShankOutline'+str(i));sc.Label='螺杆轮廓';circle(sc,0,0,1)
        previous=feature(screw,sc,'MotorShankPad'+str(i),'Pad','MountParams.MotorScrewL',True);previous.Label='螺杆'
        top=sketch(screw,'ScrewHeadTop'+str(i));top.Label='沉头顶轮廓';circle(top,0,0,1.85,re='MountParams.MotorHeadD/2')
        end=sketch(screw,'ScrewHeadEnd'+str(i),'-MountParams.HeadConeH');end.Label='沉头底轮廓';circle(end,0,0,1)
        f=screw.newObject('PartDesign::AdditiveLoft','ScrewHeadLoft'+str(i));f.Label='沉头';f.Profile=top;f.Sections=[end];f.Ruled=True;f.Refine=True
        d.recompute();assert f.Shape.isValid() and len(f.Shape.Solids)==1
        top.Visibility=False;end.Visibility=False;previous.Visibility=False
        for target in [b,board,d.Motor]:assert screw.Shape.common(target.Shape).Volume<1e-7
        screws.append(screw)
    Part.export([b,base],str(ROOT/'models/支架.step'))
    Part.export([b,base,d.Motor]+screws,str(ROOT/'models/装配.step'))
    board.Visibility=False
    (ROOT/'reports/mount_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report
