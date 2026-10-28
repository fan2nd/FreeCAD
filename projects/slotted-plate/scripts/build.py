from pathlib import Path
import sys, json
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A, Part, Sketcher
ROOT=Path(__file__).resolve().parents[1]
for folder in ('models','previews','reports'): (ROOT/folder).mkdir(exist_ok=True)
doc=A.newDocument('SlottedPlate'); doc.Label='槽板组件'
sheet=doc.addObject('Spreadsheet::Sheet','Parameters'); sheet.Label='尺寸参数'
rows=[('C1','底板宽',70),('C2','底板长',220),('C3','底板厚',8),('H1','底板安装孔径',4.5),('H2','孔横距',32),('H3','孔纵距',40),('H4','上排孔距顶边',14),('C4','槽圆弧半径',9.3),('C5','槽长',92),('C6','槽起点距尾边',19),('C7','笔沉入深度',3),('A1','推力计宽',60),('A2','推力计长',80),('A3','推力计厚',20),('A4','测力轴直径',8),('A5','测力轴伸出长',10),('B1','笔身圆弧直径',18),('B2','笔身长',90),('B3','笔截面总高',26),('B4','笔肩直径',12),('B5','笔肩长',10),('B6','T杆直径',5),('B7','T杆长',7),('B8','T头直径',12),('B9','T头长',3),('B10','笔尾直径',10),('B11','笔尾长',8),('P1','笔主体起点距尾边',2),('H5','推力计底孔深',6),('H6','推力计底孔径',4),('A6','测力轴中心距机底',6),('C8','笔槽区抬高',2.31),('D1','截面相切角',75),('C9','推力计端收短',10.4),('H7','螺丝处板厚',6),('H8','杯头沉孔直径',7.3),('H9','杯头直径',6.7),('H10','杯头高度',3.6),('H11','杯头沉孔深度',2)]
measured=json.loads((ROOT/'scripts'/'measurements.json').read_text())['confirmed']
rows=[(key,('笔截面横向总宽' if key=='B3' else name),measured.get(key,value)) for key,name,value in rows]
formulas={'H8':'=Dim_H9+0.6','H11':'=Dim_C3-Dim_H7','C2':'=Dim_P1+Dim_B2+Dim_B5+Dim_B7+Dim_B9+Dim_A5+Dim_A2-Dim_C9','C4':'=Dim_B1/2+0.3','C6':'=Dim_P1','C8':'=Dim_A6-Dim_B1/2+Dim_C7','B3':'=Dim_B1/2*(1+1/sin(Dim_D1*1 deg/2))'}

for col,val in zip('ABCD',('参数','数值','单位','说明')): sheet.set(col+'1',val)
for i,(key,name,value) in enumerate(rows,2):
 sheet.set('A'+str(i),key+' '+name);sheet.set('B'+str(i),str(value));sheet.setAlias('B'+str(i),'Dim_'+key);sheet.set('C'+str(i),'deg' if key=='D1' else 'mm');sheet.set('D'+str(i),'实测/已确认；驱动模型' if key in measured else ('收短方案设计值；驱动模型' if key in ('P1','C9') else ('推导；依赖未确认项' if key in ('C2','C4','C6') else ('设计间隙单边0.3；驱动模型' if key=='H8' else '几何推导；已确认方案' if key in formulas else '未确认；仅占位，不作加工依据'))))
for i,(key,name,value) in enumerate(rows,2):
 if key in formulas:sheet.set('B'+str(i),formulas[key])
doc.recompute()

sheet.setColumnWidth('A',190);sheet.setColumnWidth('B',85);sheet.setColumnWidth('C',65);sheet.setColumnWidth('D',180)
notes=doc.addObject('Spreadsheet::Sheet','Notes');notes.Label='说明'
for i,(a,b) in enumerate([('端部收短','笔尾侧较原方案缩短18；推力计端缩短10.4。板长233、宽70。外排孔距板端7。两参考设备略有悬出。'),('尺寸状态','实测项已写入；其余仅保留占位几何，并非用户确认尺寸。参数表驱动草图、拉伸与切除。'),('结构','推力计与笔沿共同轴线放置于底板；笔局部沉入盲槽以限制横向移动。'),('笔外形','圆直径22.2与75度夹角两直线相切；尖角朝板面侧向，圆侧沉入。横向总宽由公式计算，替代27。'),('接触','T头与测力轴端面暂设接触；未设置预压或加载行程。'),('底孔','推力计底部四个盲孔只表示安装位置；按M4安装位置表示，孔深仍待确认。底板为对应通孔，底面四个圆柱浅沉孔保留6mm板厚；实测杯头6.7×3.6，沉孔直径7.3、深2，杯头露出底面1.6。'),('长槽','圆弧盲槽，保留底部材料；槽底与笔底相切，槽半径比笔底圆弧大0.3。'),('状态','推力计和笔是外形参考实体；底板是待定设计，未作为可直接加工图交付。')],1): notes.set('A'+str(i),a);notes.set('B'+str(i),b)
notes.setColumnWidth('A',100);notes.setColumnWidth('B',680)
def expr(key): return 'Parameters.Dim_'+key+' * 1 mm'
def e(o,p,s):o.setExpression(p,s)
def body(name,label,z):
 b=doc.addObject('PartDesign::Body',name);b.Label=label;e(b,'Placement.Base.z',z);return b
def rect(b,name,w,h,x,y,z='0 mm'):
 s=doc.addObject('Sketcher::SketchObject',name);b.addObject(s);s.Label=name
 pts=[(0,0),(10,0),(10,10),(0,10)]
 for i in range(4):
  p,q=pts[i],pts[(i+1)%4];s.addGeometry(Part.LineSegment(A.Vector(*p,0),A.Vector(*q,0)),False)
 for i in range(4):s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%4,1))
 for i in (0,2):s.addConstraint(Sketcher.Constraint('Horizontal',i))
 for i in (1,3):s.addConstraint(Sketcher.Constraint('Vertical',i))
 s.addConstraint(Sketcher.Constraint('Coincident',0,1,-1,1))
 for typ,g,val,ex in [('Distance',0,10,w),('Distance',1,10,h)]:
  c=s.addConstraint(Sketcher.Constraint(typ,g,val));e(s,'Constraints['+str(c)+']',ex)
 for axis,ex in zip('xyz',(x,y,z)):e(s,'Placement.Base.'+axis,ex)
 doc.recompute();return s
def feature(b,s,name,thick,pocket=False):
 o=b.newObject('PartDesign::Pocket' if pocket else 'PartDesign::Pad',name);o.Label=name;o.Profile=s;e(o,'Length',thick);doc.recompute();s.Visibility=False
 for obj in b.Group:
  if obj!=o and hasattr(obj,'ViewObject'):obj.Visibility=False
 return o
def holes(b,thick,diameter="H1",name="螺丝孔"):
 s=doc.addObject('Sketcher::SketchObject','HoleSketch');b.addObject(s);s.Label='沉孔轮廓' if name=='杯头沉孔' else '孔位';e(s,'Placement.Base.z',thick)
 for sign in (-1,1):
  for lower in (False,True):
   i=s.addGeometry(Part.Circle(A.Vector(sign*16,176-(40 if lower else 0),0),A.Vector(0,0,1),2),False)
   for typ,val,ex in [('DistanceX',sign*16,str(sign)+' * ('+expr('H2')+') / 2'),('DistanceY',176-(40 if lower else 0),expr('C2')+' + '+expr('C9')+' - '+expr('H4')+(' - '+expr('H3') if lower else ''))]:
    c=s.addConstraint(Sketcher.Constraint(typ,i,3,val));e(s,'Constraints['+str(c)+']',ex)
   c=s.addConstraint(Sketcher.Constraint('Diameter',i,4));e(s,'Constraints['+str(c)+']',expr(diameter))
 return feature(b,s,name,thick,True)
# Axial sketches use local XY mapped to global XZ; normal points toward -Y.
axis=expr('C3')+' + '+expr('C8')+' + '+expr('B1')+'/2 - '+expr('C7')
def circle_sketch(b,name,diam,y,zc):
 sk=doc.addObject('Sketcher::SketchObject',name);b.addObject(sk);sk.Label=name
 sk.Placement.Rotation=A.Rotation(A.Vector(1,0,0),90)
 e(sk,'Placement.Base.y',y);e(sk,'Placement.Base.z',zc)
 sk.addGeometry(Part.Circle(A.Vector(0,0,0),A.Vector(0,0,1),5),False)
 sk.addConstraint(Sketcher.Constraint('Coincident',0,3,-1,1))
 k=sk.addConstraint(Sketcher.Constraint('Diameter',0,10));e(sk,'Constraints['+str(k)+']',diam)
 return sk
c=body('Base','底板','0 mm')
feature(c,rect(c,'底板轮廓',expr('C1'),expr('C2'),'-('+expr('C1')+')/2','0 mm'),'底板拉伸',expr('C3'))
feature(c,rect(c,'抬高区轮廓',expr('C1'),expr('P1')+' + '+expr('B2')+' + '+expr('B5'),'-('+expr('C1')+')/2','0 mm',expr('C3')),'笔槽抬高',expr('C8'))
groove=circle_sketch(c,'槽截面',expr('C4')+'*2',expr('C6'),axis+' + '+expr('C4')+' - '+expr('B1')+'/2')
feature(c,groove,'笔槽',expr('C5'),True)
holes(c,expr('C3'))
cb=holes(c,expr('H11'),'H8','杯头沉孔')
a=body('Gauge','推力计',expr('C3'))
feature(a,rect(a,'机身轮廓',expr('A1'),expr('A2'),'-('+expr('A1')+')/2',expr('C2')+' + '+expr('C9')+' - '+expr('A2')),'机身',expr('A3'))
shaft=circle_sketch(a,'测力轴截面',expr('A4'),expr('C2')+' + '+expr('C9')+' - '+expr('A2'),expr('A6'))
feature(a,shaft,'测力轴',expr('A5'))
# Blind mounting holes enter from the underside.
hp=holes(a,expr('H5'));hp.Label='底部安装孔'
hp.Profile[0].setExpression('Placement.Base.z','0 mm');hp.Reversed=True
for idx in (2,5,8,11):hp.Profile[0].setExpression('Constraints['+str(idx)+']',expr('H6'))
doc.recompute()
b=body('Pen','笔','0 mm')
back=expr('P1');front=back+' + '+expr('B2')
sk=circle_sketch(b,'笔身截面',expr('B1'),front,axis)
feature(b,sk,'笔身',expr('B2'))
# A circle and two tangent lines at D1 form the pen profile. Apex points
# sideways parallel to the board, not upward. Union preserves native pad history.
sk=doc.addObject('Sketcher::SketchObject','TangentProfile');b.addObject(sk);sk.Label='相切角截面'
sk.Placement.Rotation=A.Rotation(A.Vector(1,0,0),90);e(sk,'Placement.Base.y',front);e(sk,'Placement.Base.z',axis)
pts=[(6.75,-8.8),(6.75,8.8),(18.2,0)]
for i in range(3):
 p,q=pts[i],pts[(i+1)%3];sk.addGeometry(Part.LineSegment(A.Vector(*p,0),A.Vector(*q,0)),False)
for i in range(3):sk.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%3,1))
sk.addConstraint(Sketcher.Constraint('Vertical',0))
xt=expr('B1')+'/2*sin(Parameters.Dim_D1*1 deg/2)'
zt=expr('B1')+'/2*cos(Parameters.Dim_D1*1 deg/2)'
for typ,geo,pos,val,ex in [('DistanceX',0,1,6.75,xt),('DistanceY',0,1,-8.8,'-('+zt+')'),('DistanceY',0,2,8.8,zt),('DistanceX',1,2,18.2,expr('B3')+' - '+expr('B1')+'/2'),('DistanceY',1,2,0,'0 mm')]:
 k=sk.addConstraint(Sketcher.Constraint(typ,geo,pos,val));e(sk,'Constraints['+str(k)+']',ex)
feature(b,sk,'相切侧面',expr('B2'))
for name,diam,length,y in [('笔尾','B10','B11',back),('笔肩','B4','B5',front+' + '+expr('B5')),('T杆','B6','B7',front+' + '+expr('B5')+' + '+expr('B7')),('T头','B8','B9',front+' + '+expr('B5')+' + '+expr('B7')+' + '+expr('B9'))]:
 feature(b,circle_sketch(b,name+'截面',expr(diam),y,axis),name,expr(length))

doc.recompute()
report={}
for obj in (a,b,c):
 assert obj.Shape.isValid() and len(obj.Shape.Solids)==1,obj.Label
 report[obj.Label]={'valid':True,'volume':obj.Shape.Volume,'solids':len(obj.Shape.Solids)}
# Check a spreadsheet edit propagates through pad and pocket dependencies.
vol=c.Shape.Volume;sheet.set('B2','72');doc.recompute();assert c.Shape.Volume>vol
sheet.set('B2','70');doc.recompute();assert abs(c.Shape.Volume-vol)<1e-6
report['parameter_recompute']=True
assert not [o.Name for o in doc.Objects if 'Invalid' in o.State]
report['sketch_dof']={o.Label:o.FullyConstrained for o in doc.Objects if o.TypeId=='Sketcher::SketchObject'}
for one,two in ((a,b),(a,c),(b,c)):
 overlap=one.Shape.common(two.Shape).Volume;assert overlap<1e-6,(one.Label,two.Label,overlap)
report['no_solid_overlap']=True
report['axis_height_above_base']=float(sheet.get('Dim_A6'))
report['pen_burial']=float(sheet.get('Dim_C7'))
report['raised_region']=float(sheet.get('Dim_C8'))
report['cross_section_total_width']=float(sheet.get('Dim_B3'))
report['shoulder_to_raised_surface']=float(sheet.get('Dim_A6'))-float(sheet.get('Dim_B4'))/2-float(sheet.get('Dim_C8'))
report['base_dimensions']=[c.Shape.BoundBox.XLength,c.Shape.BoundBox.YLength,c.Shape.BoundBox.ZLength]
report['print_bed']=[256,256]
assert report['base_dimensions'][0]<=256 and report['base_dimensions'][1]<=256
report['outer_hole_center_to_end']=float(sheet.get('Dim_H4'))-float(sheet.get('Dim_C9'))
assert report['outer_hole_center_to_end']-float(sheet.get('Dim_H1'))/2>=4
report['screw_seat']={'count':4,'remaining_thickness':float(sheet.get('Dim_C3'))-cb.Length.Value,'recess_diameter':float(sheet.get('Dim_H8')),'recess_depth':cb.Length.Value,'head_protrusion':float(sheet.get('Dim_H10'))-cb.Length.Value}
assert abs(report['screw_seat']['remaining_thickness']-6)<1e-6
# The removed volume must be four annuli, leaving the upper six mm intact.
import math
expected=4*math.pi/4*(float(sheet.get('Dim_H8'))**2-float(sheet.get('Dim_H1'))**2)*cb.Length.Value
assert abs((cb.BaseFeature.Shape.Volume-cb.Shape.Volume)-expected)<1e-5
report['confirmed']=measured
report['derived']={k:sheet.get('Dim_'+k) for k in formulas}
(ROOT/'reports'/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
Part.export([a,b,c],str(ROOT/'models'/'槽板组件.step'))
Part.export([c],str(ROOT/'models'/'底板.step'))
import MeshPart
(ROOT/'print').mkdir(exist_ok=True)
mesh=MeshPart.meshFromShape(Shape=c.Shape,LinearDeflection=0.05,AngularDeflection=0.15,Relative=False)
assert mesh.isSolid();mesh.write(str(ROOT/'print'/'底板.stl'))
if A.GuiUp:
 import FreeCADGui as G
 for obj,color in ((a,(0.76,0.8,0.87)),(b,(0.93,0.65,0.25)),(c,(0.32,0.58,0.68))):
  obj.Visibility=True;obj.Tip.Visibility=True;obj.Tip.ViewObject.ShapeColor=color
 G.updateGui();G.activeDocument().activeView().viewAxonometric();G.activeDocument().activeView().fitAll();G.Selection.clearSelection();G.updateGui()
doc.recompute();doc.saveAs(str(ROOT/'models'/'槽板组件.FCStd'))
if A.GuiUp and not globals().get('DEFER_VIEW',False):G.activeDocument().activeView().saveImage(str(ROOT/'previews'/'assembly.png'),1200,1000,'White')
# Keep the numbered dimension sheet synchronized with the default parameters.
dimfile=ROOT/'scripts'/'dimensions.py'
exec(compile(dimfile.read_text(),str(dimfile),'exec'),{'__file__':str(dimfile)})
