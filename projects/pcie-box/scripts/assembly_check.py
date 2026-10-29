from pathlib import Path
import json
import FreeCAD as A, FreeCADGui as Gui, Part, Sketcher
from PySide import QtCore
ROOT=Path(__file__).resolve().parents[1]
doc=A.ActiveDocument
if doc is None or doc.getObject('Base') is None:
 doc=A.openDocument(str(ROOT/'models'/'网卡收纳盒.FCStd'))
doc.Label='网卡收纳盒'
p=doc.getObject('Parameters')
# Reuse the exact native sketch and feature constructors used for the enclosure.
source=(ROOT/'scripts'/'build.py').read_text()
exec(source[source.index('def q(k):'):source.index("base=doc.addObject")])
base=doc.getObject('Base');lid=doc.getObject('Lid')
cp=doc.addObject('Spreadsheet::Sheet','CardParameters');cp.Label='网卡参数'
rows=[('BoardL','PCB板长',166,'mm','实测'),('BoardT','PCB板厚',1.6,'mm','设计假定'),('CoverH','金属壳上方包络',14,'mm','用户实测；包含散热片，不另建散热片'),('ScrewH','六颗螺丝凸起','=Parameters.Dim_ScrewH','mm','用户实测；与底座支撑共用尺寸'),('MountH','挡片侧两颗凸起','=Parameters.Dim_Back','mm','用户实测；与底座支撑共用尺寸'),('ScrewD','六颗螺丝头直径',5.6,'mm','照片估算'),('MountD','挡片侧螺丝头直径',5.6,'mm','照片估算'),('BracketT','挡片厚度',1,'mm','设计假定'),('BracketRise','挡片高出金属壳',1,'mm','用户实测'),('EarRise','固定耳高出挡片',3.58,'mm','PCIe CEM 3.0 图9-9，局部轮廓参考'),('EarWidth','固定耳宽',18.59,'mm','PCIe CEM 3.0 图9-9'),('SlotW','耳槽宽',4.42,'mm','PCIe CEM 3.0 图9-9'),('BracketH','挡片投影高度',73.45,'mm','按用户纠正，上端与PCB顶边齐平；下端沿用照片位置'),('ComponentH','背面元件包络',1,'mm','照片未测高；用于检查，非实测'),('SFPOut','SFP外伸',2.5,'mm','用户实测；从挡片外侧面起'),('SFPOffset','SFP宽向偏移',10,'mm','用户实测；以邻近PCB直角边为基准'),('SFPWidth','SFP接口宽',14,'mm','包络估算'),('SFPHeight','SFP接口高',11.5,'mm','包络估算')]
for c,v in zip('ABCD',('参数','数值','单位','依据')):cp.set(c+'1',v)
for i,(key,label,value,unit,note) in enumerate(rows,2):
 cp.set('A'+str(i),label);cp.set('B'+str(i),str(value));cp.setAlias('B'+str(i),'Dim_'+key);cp.set('C'+str(i),unit);cp.set('D'+str(i),note)
cp.setColumnWidth('A',170);cp.setColumnWidth('D',360)
def cq(k):return '(CardParameters.Dim_'+k+' * 1 mm)'
B=F+'+'+q('Support');TOP=B+'+'+cq('BoardT')
card=doc.addObject('App::Part','Card');card.Label='网卡'
parts=[]
def body(name,label,color):
 b=doc.addObject('PartDesign::Body',name);b.Label=label;card.addObject(b);parts.append((b,color));return b

def poly(s,points):
 for i,(x,y) in enumerate(points):
  u,v=points[(i+1)%len(points)];s.addGeometry(Part.LineSegment(A.Vector(x,y,0),A.Vector(u,v,0)),False)
 for i,(x,y) in enumerate(points):
  s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%len(points),1))
  for typ,val in [('DistanceX',x),('DistanceY',y)]:
   n=s.addConstraint(Sketcher.Constraint(typ,i,1,val));s.setExpression('Constraints[%d]'%n,str(val)+(' * CardParameters.Dim_BoardL / 166 * 1 mm' if typ=='DistanceX' else ' * 1 mm'))
 doc.recompute();return s
pcb=body('PCB','PCB',(0.06,0.43,0.24))
outline=[(-77,33.45),(89,33.45),(89,-22),(16,-22),(16,-35.45),(-22,-35.45),(-22,-28),(-24,-28),(-24,-35.45),(-35,-35.45),(-35,-22),(-40,-22),(-40,-30),(-47,-30),(-47,-22),(-65,-22),(-65,-30),(-77,-30)]
feat(pcb,poly(sketch(pcb,'PCB轮廓',B),outline),'PCB板',cq('BoardT'))
# Metal housing is a conservative solid occupancy envelope, no heatsink or decorative electronics.
cover=body('Cover','金属壳',(0.72,0.74,0.76))
feat(cover,rectangle(sketch(cover,'金属壳轮廓',TOP),cq('BoardL'),'55 mm','6 mm','5.7 mm'),'金属壳包络',cq('CoverH'))
# Main bracket and its folded tabs are represented by connected native pads.
bracket=body('Bracket','挡片',(0.64,0.67,0.70))
BTOP=TOP+'+'+cq('CoverH')+'+'+cq('BracketRise')
ETOP=BTOP+'+'+cq('EarRise')
feat(bracket,rectangle(sketch(bracket,'挡片轮廓',B+'-2 mm'),cq('BracketT'),cq('BracketH'),'-79.5 mm','-3.275 mm'),'挡片主体',cq('BoardT')+'+'+cq('CoverH')+'+'+cq('BracketRise')+'+2 mm')
feat(bracket,rectangle(sketch(bracket,'折耳轮廓',ETOP+'-'+cq('EarWidth')),'12 mm',cq('BracketT'),'-85 mm','32.95 mm'),'折耳',cq('EarWidth'))
# The folded ear lies in XZ. Its screw notch opens upwards in Z.
def ear_sketch(name):
 ss=sketch(bracket,name,'0 mm');ss.Placement.Rotation=A.Rotation(A.Vector(1,0,0),90)
 ss.Placement.Base.y=33.45
 return ss
ss=ear_sketch('耳槽圆底轮廓')
n=ss.addGeometry(Part.Circle(A.Vector(-85.35,20.73,0),A.Vector(0,0,1),2.21),False)
for spec,expr in [(('DistanceX',n,3,-85.35),'-85.35 mm'),(('DistanceY',n,3,20.73),ETOP+'-4.45 mm'),(('Diameter',n,4.42),cq('SlotW'))]:
 j=ss.addConstraint(Sketcher.Constraint(*spec));ss.setExpression('Constraints[%d]'%j,expr)
feat(bracket,ss,'耳槽圆底',cq('BracketT'),'Pocket',True)
ss=ear_sketch('耳槽开口轮廓')
rectangle(ss,cq('SlotW'),'5 mm','-85.35 mm',ETOP+'-1.95 mm')
feat(bracket,ss,'耳槽开口',cq('BracketT'),'Pocket',True)
s=sketch(bracket,'安装片轮廓',B+'-0.7 mm')
for yy in ('29 mm','-25.5 mm'):rectangle(s,'15 mm','7 mm','-72.5 mm',yy)
feat(bracket,s,'安装片','0.7 mm')
# Two SFP connector envelopes on the outside of the bracket.
for idx in (1,2):
 yy='-30 mm+'+cq('SFPOffset')+'+'+cq('SFPWidth')+'/2+'+str((idx-1)*15)+' mm'
 b=body('SFP'+str(idx),'SFP接口'+str(idx),(0.58,0.61,0.63))
 feat(b,rectangle(sketch(b,'接口轮廓',TOP),cq('SFPOut')+'+1 mm',cq('SFPWidth'),'-79.5 mm-'+cq('SFPOut')+'/2',yy),'接口包络',cq('SFPHeight'))
 # Opening on the left-facing plane; sketch normal is +X, pocket reversed inward.
 ss=sketch(b,'端口轮廓','0 mm');ss.Placement.Rotation=A.Rotation(A.Vector(0,1,0),90)
 ss.setExpression('Placement.Base.x','-80 mm-'+cq('SFPOut'))
 rectangle(ss,cq('SFPHeight')+'-2 mm',cq('SFPWidth')+'-2 mm','-('+TOP+'+'+cq('SFPHeight')+'/2)',yy)
 feat(b,ss,'端口','2 mm','Pocket',True)
# Screw centers measured from PCB upper-left in backside view; mirrored to front-model coordinates.
screw_positions=[(86,28.45),(37.5,28.45),(-24.5,28.45),(86,-17.55),(37.5,-17.55),(-24.5,-17.55),(-71,28.45),(-71,-26.05)]
for idx,(x,y) in enumerate(screw_positions,1):
 b=body('Screw'+str(idx),'螺丝'+str(idx),(0.7,0.73,0.76));s=sketch(b,'螺丝头轮廓',B)
 n=s.addGeometry(Part.Circle(A.Vector(x,y,0),A.Vector(0,0,1),2.8),False)
 for spec,expr in [(('DistanceX',n,3,x),str(x)+' * CardParameters.Dim_BoardL / 166 * 1 mm'),(('DistanceY',n,3,y),str(y)+' mm'),(('Diameter',n,5.6),cq('ScrewD' if idx<=6 else 'MountD'))]:
  j=s.addConstraint(Sketcher.Constraint(*spec));s.setExpression('Constraints[%d]'%j,expr)
 feat(b,s,'螺丝头',cq('ScrewH' if idx<=6 else 'MountH'),rev=True)
# Golden contact bands, separately editable and clear of the key notch.
for idx,(xl,xr) in enumerate([(-35,-24),(-22,16)],1):
 b=body('Contact'+str(idx),'金手指'+str(idx),(0.85,0.67,0.20))
 feat(b,rectangle(sketch(b,'金手指轮廓',TOP),'%s mm'%(xr-xl),'5.8 mm','%s mm'%((xl+xr)/2),'-32.5 mm'),'触点','0.03 mm')
# Only representative backside component regions visible in the supplied photo.
for idx,(x,y,w,h) in enumerate([(48,3,10,9),(18,2,10,14),(-7,-10,12,10),(55,-15,12,7)],1):
 b=body('BackComponent'+str(idx),'背面元件'+str(idx),(0.17,0.18,0.19))
 feat(b,rectangle(sketch(b,'元件范围',B),str(w)+' mm',str(h)+' mm',str(x)+' mm',str(y)+' mm'),'元件包络',cq('ComponentH'),rev=True)
doc.recompute()
result={'basis':'PCB长166、上方14、六颗螺丝1、挡片侧两颗2为实测；螺丝位置按用户实测，头径按照片估算；元件区高度1及板厚1.6是假定；挡片高出壳1、SFP外伸2.5及宽向偏移10为用户尺寸；SFP宽14、高11.5为示意估算。固定耳轮廓参考PCIe CEM 3.0图9-9。','parts':[],'collisions':[]}
for b,col in parts:
 assert b.Shape.isValid() and len(b.Shape.Solids)==1,b.Label
 for o in b.Group:o.Visibility=False
 b.Visibility=True;b.Tip.Visibility=True;b.Tip.ViewObject.ShapeColor=col;b.Tip.ViewObject.LineColor=(0.12,0.15,0.16)
 checks={}
 for shell in (base,lid):
  vol=b.Shape.common(shell.Shape).Volume;dist=b.Shape.distToShape(shell.Shape)[0];checks[shell.Label]={'intersection_mm3':vol,'distance_mm':dist}
  if vol>1e-6:result['collisions'].append({'card_part':b.Label,'case_part':shell.Label,'volume_mm3':vol})
 result['parts'].append({'name':b.Label,'checks':checks})
assert not result['collisions'], result['collisions']
assert cover.Shape.distToShape(lid.Shape)[0]<1e-6
for idx in range(1,9):
 assert doc.getObject('Screw'+str(idx)).Shape.distToShape(base.Shape)[0]<1e-6
result['cover_contact']=True;result['eight_screw_contacts']=True
assert bracket.Shape.BoundBox.ZMax < lid.Shape.BoundBox.ZMax
result['bracket_below_lid_top_mm']=lid.Shape.BoundBox.ZMax-bracket.Shape.BoundBox.ZMax
result['ear_roof_mm']=float(p.Dim_Lid)-float(p.Dim_EarDepth)
assert result['ear_roof_mm']>=2-1e-6
result['fully_constrained']=all(o.FullyConstrained for o in doc.Objects if o.TypeId=='Sketcher::SketchObject')
assert result['fully_constrained']
notes=doc.addObject('Spreadsheet::Sheet','FitNotes');notes.Label='装配检查'
for i,(k,v) in enumerate([('依据',result['basis']),('方向','背面照片挡片在右；模型已镜像为挡片在左，与原正面照片一致。'),('检查范围','逐件检查PCB、金属壳包络、挡片、8颗螺丝、金手指和代表性背面元件与上下盒交集。并非实物装配保证。'),('干涉数量',str(len(result['collisions']))),('结果',json.dumps(result['collisions'],ensure_ascii=False)),('显示','默认闭合装配。网卡为装配组件，可展开编辑；不包含散热片。')],1):notes.set('A'+str(i),k);notes.set('B'+str(i),v)
notes.setColumnWidth('A',100);notes.setColumnWidth('B',800)
(ROOT/'reports'/'assembly_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
Part.export([b for b,c in parts],str(ROOT/'models'/'网卡.step'))
Part.export([base,lid]+[b for b,c in parts],str(ROOT/'models'/'网卡收纳盒.step'))
Gui.Selection.clearSelection();view=Gui.activeDocument().activeView()
def settle():
 loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(400,loop.quit);loop.exec_();Gui.updateGui()
lid.Visibility=False;view.viewTop();view.fitAll();settle();view.saveImage(str(ROOT/'previews'/'装配俯视.png'),1600,1000,'White')
view.viewAxonometric();view.fitAll();settle();view.saveImage(str(ROOT/'previews'/'装配内部.png'),1600,1000,'White')
base.Visibility=False;view.viewBottom();view.fitAll();settle();view.saveImage(str(ROOT/'previews'/'网卡背面.png'),1600,1000,'White')
view.viewFront();view.fitAll();settle();view.saveImage(str(ROOT/'previews'/'挡片侧视.png'),1800,700,'White')
base.Visibility=True;lid.Visibility=True;view.viewAxonometric();view.fitAll();settle()
doc.recompute();doc.saveAs(str(ROOT/'models'/'网卡收纳盒.FCStd'))
print('ASSEMBLY_CHECK',json.dumps(result['collisions'],ensure_ascii=False))

exec(compile((ROOT/'scripts'/'show_fit.py').read_text(),str(ROOT/'scripts'/'show_fit.py'),'exec'),{'__file__':str(ROOT/'scripts'/'show_fit.py')})
