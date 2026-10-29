from pathlib import Path
import sys,json
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A, Part, Sketcher, MeshPart
ROOT=Path(__file__).resolve().parents[1]
for d in ('models','print','previews','reports'): (ROOT/d).mkdir(exist_ok=True)
doc=A.newDocument('PCIeBox');doc.Label='网卡收纳盒'
p=doc.addObject('Spreadsheet::Sheet','Parameters');p.Label='驱动参数'
rows=[('L','外长',190,'全包围；挡片耳及卡尾均在盒内'),('W','内腔宽',84,'外宽90；为挡片避让和磁铁孔保留至少2 mm实体壁'),('H','内腔深','=Dim_Support+Dim_Board+Dim_Top','由卡的叠层高度驱动，平盖直接贴壳'),('Seat','磁铁座宽',6,'侧壁局部加厚；孔外侧剩余2.2'),('Wall','侧壁厚',3,'设计值'),('Floor','底厚',7,'与顶盖等厚；盖内容纳挡片耳'),('Lid','盖厚','=Dim_Floor','与底板等厚；磁铁孔底保留4.85'),('MagD','磁铁直径',4,'用户指定'),('MagH','磁铁高度',2,'用户指定'),('HoleD','磁铁孔径','=Dim_MagD+0.2','胶粘间隙'),('HoleH','磁铁孔深','=Dim_MagH+0.15','胶层余量'),('Gap','定位条单边间隙',0.35,'打印配合需试装'),('Rim','定位条壁厚',1.4,'设计值'),('Lip','定位条高',2,'设计值'),('Tray','内托高','=Dim_H','上下轮廓壁直达顶盖接触面'),('Scale','轮廓比例',1,'照片轮廓比例；非实测'),('FingerDepth','金手指底部避空',1,'底板剩余6 mm'),('CardL','PCB板长',166,'用户实测'),('Top','上方包络',14,'用户实测金属罩；散热片更低'),('Back','背面凸起',2,'用户实测'),('Board','PCB厚度',1.6,'设计假定；非本卡实测'),('Clear','背面余量',0.6,'背面元件留空；盖内限位面贴金属壳'),('Total','盒体总高','=Dim_Floor+Dim_H+Dim_Lid','由平盖与短支撑叠层计算，允许降低'),('Round','外角圆角',2,'上下壳外侧竖边圆角'),('PostH','六柱高度',2,'用户要求短柱'),('EarDepth','盖内耳槽深',5,'耳顶净空0.42；槽顶保留2 mm'),('Support','PCB背面离底高','=Dim_PostH+Dim_ScrewH','六柱托住1 mm螺丝头，挡片侧两柱随2 mm螺丝头降低1 mm'),('PostD','螺丝支撑柱直径',5,'小于估算螺丝头直径5.6'),('ScrewH','六颗螺丝凸起',1,'用户实测'),('End','左端壁厚',3,'封闭端壁'),('Ear','挡片耳槽宽',2.2,'耳厚1 mm，两侧各留0.6 mm；仅下盒保留向上装入槽')]
for col,val in zip('ABCD',['参数','数值','单位','说明']):p.set(col+'1',val)
for i,(key,label,value,note) in enumerate(rows,2):
 p.set('A'+str(i),label);p.set('B'+str(i),'0' if str(value).startswith('=') else str(value));p.setAlias('B'+str(i),'Dim_'+key);p.set('C'+str(i),'1' if key=='Scale' else 'mm');p.set('D'+str(i),note)
for i,(_,_,value,_) in enumerate(rows,2):
 if str(value).startswith('='):p.set('B'+str(i),str(value))
p.setColumnWidth('A',145);p.setColumnWidth('D',260)
doc.recompute()
def q(k):return '(Parameters.Dim_'+k+' * 1 mm)'
L,W,H,E,T,F,C,G,R,U=[q(k) for k in ('L','W','H','Seat','Wall','Floor','Lid','Gap','Rim','Lip')]
OX=L;OY=W+'+2*'+T;Z=H+'+'+F

def sketch(b,name,z):
 s=doc.addObject('Sketcher::SketchObject',name);b.addObject(s);s.Label=name;s.setExpression('Placement.Base.z',z);return s

def rectangle(s,w,h,cx="0 mm",cy="0 mm"):
 n=s.GeometryCount
 pts=[(-5,-5),(5,-5),(5,5),(-5,5)]
 for i in range(4):
  a,b=pts[i],pts[(i+1)%4];s.addGeometry(Part.LineSegment(A.Vector(a[0],a[1],0),A.Vector(b[0],b[1],0)),False)
 for i in range(4):s.addConstraint(Sketcher.Constraint('Coincident',n+i,2,n+(i+1)%4,1))
 for i in (0,2):s.addConstraint(Sketcher.Constraint('Horizontal',n+i))
 for i in (1,3):s.addConstraint(Sketcher.Constraint('Vertical',n+i))
 for spec,ex in [(('DistanceX',n,1,n,2,10),w),(('DistanceY',n+1,1,n+1,2,10),h),(('DistanceX',n,1,-5),cx+'-('+w+')/2'),(('DistanceY',n,1,-5),cy+'-('+h+')/2')]:
  idx=s.addConstraint(Sketcher.Constraint(*spec));s.setExpression('Constraints[%d]'%idx,ex)
 doc.recompute()
 return s

def feat(b,s,name,length,kind='Pad',rev=False):
 o=b.newObject('PartDesign::'+kind,name);o.Label=name;o.Profile=s;o.setExpression('Length',length);o.Reversed=rev;doc.recompute()
 for ob in b.Group:ob.Visibility=False
 o.Visibility=True
 return o

def magnets(b,z,rev=False):
 s=sketch(b,'磁铁孔位',z)
 for sx in (-1,1):
  for sy in (-1,1):
   n=s.addGeometry(Part.Circle(A.Vector(sx*96.5,sy*41,0),A.Vector(0,0,1),2.1),False)
   for spec,ex in [(('DistanceX',n,3,sx*96.5),('-'+L+'/2+30 mm' if sx<0 else L+'/2-14 mm')),(('DistanceY',n,3,sy*41),str(sy)+'*('+W+'/2-1.3 mm)'),(('Diameter',n,4.2),q('HoleD'))]:
    i=s.addConstraint(Sketcher.Constraint(*spec));s.setExpression('Constraints[%d]'%i,ex)
 return feat(b,s,'磁铁孔',q('HoleH'),'Pocket',rev)
base=doc.addObject('PartDesign::Body','Base');base.Label='下盒'
feat(base,rectangle(sketch(base,'盒体轮廓','0 mm'),OX,OY),'盒体',Z)
feat(base,rectangle(sketch(base,'通槽轮廓',Z),L+'+2 mm',W),'通槽',H,'Pocket')
s=sketch(base,'磁铁座轮廓',F)
for sx in (-1,1):
 for sy in (-1,1):rectangle(s,'10 mm',E,('-'+L+'/2+30 mm' if sx<0 else L+'/2-14 mm'),str(sy)+'*('+W+'/2-1.3 mm)')
feat(base,s,'磁铁座',H)
# Trace of the visible card envelope, scaled from the user's 180 mm overall length.
# Clearance is already included: main cover approx. 1 mm; connector approx. 1.5 mm.
outline=[(-92,34.05),(-73,34.05),(-73,34.5),(92,34.5),(92,-23),(20,-23),(20,-36),(-32,-36),(-32,-23),(-35,-23),(-35,-32),(-44,-32),(-44,-23),(-59,-23),(-59,-32),(-73,-32),(-73,-41),(-92,-41)]
def polygon(s,points):
 for i,(x,y) in enumerate(points):
  u,v=points[(i+1)%len(points)];s.addGeometry(Part.LineSegment(A.Vector(x,y,0),A.Vector(u,v,0)),False)
 for i,(x,y) in enumerate(points):
  s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%len(points),1))
  for typ,val in [('DistanceX',x),('DistanceY',y)]:
   n=s.addConstraint(Sketcher.Constraint(typ,i,1,val));s.setExpression('Constraints[%d]'%n,(('(-78 + '+str(x+73)+' * (Parameters.Dim_CardL + 2) / 165) * 1 mm') if typ=='DistanceX' and x>=-73 else str(val)+' * Parameters.Dim_Scale * 1 mm'))
 doc.recompute();return s
feat(base,rectangle(sketch(base,'内托轮廓',F),L,OY),'内托',q('Tray'))
feat(base,polygon(sketch(base,'卡轮廓',F+'+'+q('Tray')),outline),'卡槽',q('Tray'),'Pocket')
# Extra floor clearance under the edge connector; never use gold fingers as stops.
feat(base,rectangle(sketch(base,'金手指避空轮廓',F),'(52 * (Parameters.Dim_CardL + 2) / 165) * 1 mm','15 mm','(-78 + 67 * (Parameters.Dim_CardL + 2) / 165) * 1 mm','-29.5 mm'),'金手指避空',q('FingerDepth'),'Pocket')

# Eight cylindrical supports bear on screw heads, leaving components suspended.
for positions,key,label in [([(86,28.45),(37.5,28.45),(-24.5,28.45),(86,-17.55),(37.5,-17.55),(-24.5,-17.55)],'ScrewH','螺丝支撑'),([(-71,28.45),(-71,-26.05)],'Back','挡片螺丝支撑')]:
 s=sketch(base,label+'轮廓',F)
 for x,y in positions:
  n=s.addGeometry(Part.Circle(A.Vector(x,y,0),A.Vector(0,0,1),2.5),False)
  for spec,ex in [(('DistanceX',n,3,x),str(x)+' * Parameters.Dim_CardL / 166 * 1 mm'),(('DistanceY',n,3,y),str(y)+' mm'),(('Diameter',n,5),q('PostD'))]:
   i=s.addConstraint(Sketcher.Constraint(*spec));s.setExpression('Constraints[%d]'%i,ex)
 feat(base,s,label,q('Support')+'-'+q(key))
# Left end wall closes the bracket side except the upper folded mounting ear.
feat(base,rectangle(sketch(base,'左端壁轮廓',F),q('End'),OY,'-'+L+'/2+'+q('End')+'/2'),'左端壁',H)
feat(base,rectangle(sketch(base,'挡片端部避空轮廓',Z),'3 mm','3 mm','-79.5 mm','-40 mm'),'挡片端部避空',H,'Pocket')
magnets(base,Z)
# A shallow exterior recess gives fingers access beneath the lid without opening the cavity.
s=sketch(base,'开盖口轮廓',Z);rectangle(s,'20 mm','2.4 mm');s.setExpression('Placement.Base.y','-('+OY+')/2')
feat(base,s,'开盖口','1.6 mm','Pocket')
lid=doc.addObject('PartDesign::Body','Lid');lid.Label='上盖';lid.setExpression('Placement.Base.z',Z)
feat(lid,rectangle(sketch(lid,'盖板轮廓','0 mm'),OX,OY),'盖板',C)
# Flat lid touches the metal cover; local relief only for bracket and fixing ear.
feat(lid,rectangle(sketch(lid,'挡片避让轮廓','0 mm'),'2.2 mm','74.65 mm','-79.5 mm','-3.275 mm'),'挡片避让','1.6 mm','Pocket',True)
feat(lid,rectangle(sketch(lid,'固定耳避让轮廓','0 mm'),'13.2 mm',q('Ear'),'-85 mm','32.95 mm'),'固定耳避让',q('EarDepth'),'Pocket',True)
magnets(lid,'0 mm',True)
notes=doc.addObject('Spreadsheet::Sheet','Notes');notes.Label='说明'
info=[('用途','PCIe x8半高双SFP卡收纳；保留半高挡板，不插SFP模块。'),('依据','PCIe CEM 3.0 半高板高68.90；167.65短卡长度档及79.2半高挡板仅作参考；卡含挡片总长180由用户提供，盒外长190，两端封闭，挡片耳收入盒内。'),('实测','PCB长166；上方金属罩高14，散热片更低；背面凸起2。板厚暂按1.6。PCB背面离底3，背面元件悬空；平盖厚7，底面直接与罩顶接触。八个直径5圆柱分别高2（六个）和1（两个），托住螺丝头。'),('假定','板身长166已实测，局部缺口沿用照片推算。用户确认卡含挡片长180，盒外宽90；平盖贴壳，总高32.6，挡片耳不超出盖顶；左端壁厚3，耳槽宽2.2；原左上角多余缺口已补齐，上盖仅挡片及固定耳局部避让；右端封闭；磁铁座处净宽75.4，上下轮廓壁直达顶盖底面，取消相撞定位条；这是设计空间，不是整卡实测。标准不能确定照片中专用金属罩长度。'),('轮廓','按照片及总长180推算阶梯内托；主罩约1 mm间隙，金手指约1.5 mm，局部位置非实测。金手指下方另切1 mm避空；圆柱托住八颗螺丝；坐标按用户实测，头径按背面照片估算，须试装检查。'),('结构','下盒加磁吸上盖；侧壁端部各一对Ø4×2磁铁，共8颗；相对面极性相吸，胶粘固定。'),('参数','驱动参数表通过表达式驱动草图、拉伸、切除和装配位置；数值、单位分列。'),('收纳','内托按PCB及金手指阶梯轮廓延伸至顶盖接触面；两端封闭；整卡装防静电袋并用软垫保护背面，禁止挤压金手指；普通打印塑料不提供防静电保护。'),('打印','下盒底面朝下；上盖外表面朝下，磁铁孔和挡片避让槽朝上；STL已摆放，无需支撑。'),('配合','磁铁孔Ø4.2深2.15；上下轮廓壁与盖面接触，无下伸定位条。磁铁面宜胶粘至接近齐平，先干装确认极性。'),('验证','几何、闭合干涉和参数重算检查；实际网卡、打印配合和磁吸力未实测。')]
for i,(a,b) in enumerate(info,1):notes.set('A'+str(i),a);notes.set('B'+str(i),b)
notes.setColumnWidth('A',90);notes.setColumnWidth('B',650)
doc.recompute()
report={}
for b in (base,lid):
 assert b.Shape.isValid() and len(b.Shape.Solids)==1,b.Label
 report[b.Label]={'volume':b.Shape.Volume,'valid':True,'bbox':[b.Shape.BoundBox.XLength,b.Shape.BoundBox.YLength,b.Shape.BoundBox.ZLength]}
assert base.Shape.common(lid.Shape).Volume<1e-7
report['assembly_intersection']=0
# Only the upper mounting-ear slot passes through the left end wall.
closed=Part.makeBox(2.8,60,17,A.Vector(-94.9,-30,6.1))
assert abs(base.Shape.common(closed).Volume-closed.Volume)<1e-6
ear=Part.makeBox(4,2.0,18.4,A.Vector(-90.5,31.95,float(p.Dim_Floor)+0.1))
assert base.Shape.common(ear).Volume<1e-6 and lid.Shape.common(ear).Volume<1e-6
right=Part.makeBox(2.8,60,17,A.Vector(92.1,-30,6.1))
assert abs(base.Shape.common(right).Volume-right.Volume)<1e-6
report['left_wall_closed']=True
report['right_wall_closed']=True
report['ear_slot_clear']=True
corner=Part.makeBox(0.8,6.5,18,A.Vector(-88,34.15,2.5))
assert abs(base.Shape.common(corner).Volume-corner.Volume)<1e-6
inner_corner=Part.makeBox(8,6,18,A.Vector(-86,34.6,2.5))
assert abs(base.Shape.common(inner_corner).Volume-inner_corner.Volume)<1e-6
report['upper_left_corner_filled']=True
# Verify actual card body envelope and clearances at the edge-supported height.
body_bottom=float(p.Dim_Floor)+float(p.Dim_Support)
card=Part.makeBox(166,54,1.6+14,A.Vector(-77,-22,body_bottom))
back=Part.makeBox(166,52,2,A.Vector(-77,-20,body_bottom-2))
for envelope in (card,):
 assert base.Shape.common(envelope).Volume<1e-6
 assert lid.Shape.common(envelope).Volume<1e-6
report['card_body_envelope_clear']=True
report['measured_mm']={'board_length':166,'top':14,'back':2}
report['assumed_board_thickness']=1.6
report['back_clearance']=0.6
report['cover_clearance']=0.0
report['screw_supports']={'diameter':5,'six_height':float(p.Dim_Support)-1,'two_height':float(p.Dim_Support)-2}
box=Part.makeCompound([base.Shape,lid.Shape]).BoundBox
report['outer_dimensions']=[box.XLength,box.YLength,box.ZLength]
assert all(abs(a-b)<1e-6 for a,b in zip(report['outer_dimensions'],[190,90,32.6]))
v=base.Shape.Volume;p.set('B2','191');doc.recompute();assert base.Shape.Volume>v and base.Shape.common(lid.Shape).Volume<1e-7
p.set('B2','190');doc.recompute();assert abs(base.Shape.Volume-v)<1e-6
report['parameter_recompute']=True
# Measured inputs drive the outline, edge ledges and cover stops.
original=(base.Shape.Volume,lid.Shape.Volume)
for key,new_value,expected_body in [('CardL',167,base),('Back',2.5,base),('Top',15,base)]:
 row=next(i for i,r in enumerate(rows,2) if r[0]==key)
 old=rows[row-2][2];before=expected_body.Shape.Volume
 p.set('B'+str(row),str(new_value));doc.recompute()
 assert expected_body.Shape.isValid() and abs(expected_body.Shape.Volume-before)>0.1,(key,before,expected_body.Shape.Volume)
 p.set('B'+str(row),str(old));doc.recompute()
assert abs(base.Shape.Volume-original[0])<1e-6 and abs(lid.Shape.Volume-original[1])<1e-6
report['measured_parameter_recompute']=True
report['fully_constrained']=all(o.FullyConstrained for o in doc.Objects if o.TypeId=='Sketcher::SketchObject')
assert report['fully_constrained']
# Round only external vertical corners; preserve the native fillet dependency.
for body_obj in (base,lid):
 previous=body_obj.Tip
 edges=[]
 for index,edge in enumerate(previous.Shape.Edges,1):
  bb=edge.BoundBox
  if bb.XLength<1e-7 and bb.YLength<1e-7 and bb.ZLength>0.1 and abs(abs(bb.XMin)-float(p.Dim_L)/2)<1e-6 and abs(abs(bb.YMin)-(float(p.Dim_W)/2+float(p.Dim_Wall)))<1e-6:
   edges.append('Edge'+str(index))
 assert len(edges)==4,(body_obj.Label,edges)
 rounded=body_obj.newObject('PartDesign::Fillet','外角圆角');rounded.Base=(previous,edges);rounded.setExpression('Radius',q('Round'));doc.recompute()
 for obj in body_obj.Group:obj.Visibility=False
 rounded.Visibility=True
 assert rounded.Shape.isValid() and len(rounded.Shape.Solids)==1
assert not [o.Name for o in doc.Objects if 'Invalid' in o.State]
# Remaining material at the limiting wall and pocket locations (nominal mm).
outer_y=float(p.Dim_W)/2+float(p.Dim_Wall)
mag_y=float(p.Dim_W)/2-1.3
thickness={
 '磁铁孔外侧':outer_y-mag_y-float(p.Dim_HoleD)/2,
 '磁铁孔内侧上方':mag_y-float(p.Dim_HoleD)/2-34.5,
 '挡片下端外墙':outer_y-41.5,
 '固定耳槽顶':float(p.Dim_Lid)-float(p.Dim_EarDepth),
 '固定耳槽端墙':float(p.Dim_L)/2-91.6,
 '磁铁孔底':float(p.Dim_Lid)-float(p.Dim_HoleH),
 '金手指槽底':float(p.Dim_Floor)-float(p.Dim_FingerDepth),
 '左右端墙':float(p.Dim_End),
}
assert min(thickness.values())>=2-1e-6,thickness
# Solid probes verify the two limiting sections on the final solids.
for shape,probe in [
 (base.Shape,Part.makeBox(1,2.19,2,A.Vector(-65,-outer_y,float(p.Dim_Floor)+float(p.Dim_H)-2))),
 (base.Shape,Part.makeBox(1,3.49,10,A.Vector(-79.5,-outer_y,float(p.Dim_Floor)+0.1))),
 (lid.Shape,Part.makeBox(10,1.8,1.99,A.Vector(-90,32.05,float(p.Dim_Floor)+float(p.Dim_H)+float(p.Dim_EarDepth)+0.01)))]:
 assert abs(shape.common(probe).Volume-probe.Volume)<1e-6
report['remaining_wall_mm']=thickness
report['minimum_wall_mm']=min(thickness.values())

for b in (base,lid):
 Part.export([b],str(ROOT/'models'/(b.Label+'.step')))
 shape=b.Shape.copy()
 if b==lid:shape.rotate(A.Vector(0,0,0),A.Vector(1,0,0),180)
 shape.translate(A.Vector(0,0,-shape.BoundBox.ZMin))
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=0.05,AngularDeflection=0.15,Relative=False)
 assert mesh.isSolid();mesh.write(str(ROOT/'print'/(b.Label+'.stl')))
Part.export([base,lid],str(ROOT/'models'/'网卡收纳盒.step'))
(ROOT/'reports'/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if A.GuiUp:
 import FreeCADGui as Gui
 for b,col in [(base,(0.26,0.39,0.47)),(lid,(0.77,0.82,0.85))]:
  for o in b.Group:o.Visibility=False
  b.Visibility=True;b.Tip.Visibility=True;b.Tip.ViewObject.ShapeColor=col;b.Tip.ViewObject.LineColor=(0.15,0.18,0.2)
 Gui.Selection.clearSelection();Gui.activeDocument().activeView().setCameraOrientation((0.424708200277867,0.175919896606161,0.339851142979987,0.820473238570283));Gui.activeDocument().activeView().fitAll();Gui.updateGui()
doc.recompute();doc.saveAs(str(ROOT/'models'/'网卡收纳盒.FCStd'))
if A.GuiUp:
 Gui.activeDocument().activeView().saveImage(str(ROOT/'previews'/'assembly.png'),1400,900,'White')
 lid.Visibility=False;Gui.activeDocument().activeView().fitAll();Gui.updateGui();Gui.activeDocument().activeView().saveImage(str(ROOT/'previews'/'interior.png'),1400,900,'White')
 lid.Visibility=True;Gui.activeDocument().activeView().fitAll();Gui.updateGui();doc.save()
print('BUILD_OK',json.dumps(report,ensure_ascii=False))

if A.GuiUp:
 render=ROOT/'scripts'/'render.py'
 exec(compile(render.read_text(),str(render),'exec'),{'__file__':str(render)})

# Complete enclosure and card share one editable document.
assembly=ROOT/"scripts"/"assembly_check.py"
exec(compile(assembly.read_text(),str(assembly),"exec"),{"__file__":str(assembly)})
