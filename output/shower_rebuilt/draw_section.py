import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).parent;g=json.loads((p/'section_geometry.json').read_text());S=2
im=Image.new('RGB',(1500*S,900*S),'#f5f7fa');d=ImageDraw.Draw(im)
fontpath='/System/Library/Fonts/STHeiti Medium.ttc'
def font(n):return ImageFont.truetype(fontpath,n*S)
def text(x,y,t,n=22,col='#263449'):d.text((x*S,y*S),t,font=font(n),fill=col)
def line(points,col,width=2):d.line([(x*S,y*S) for x,y in points],fill=col,width=max(1,int(width*S)))
def circle(cx,cy,r,col=None,outline=None,width=2):d.ellipse(((cx-r)*S,(cy-r)*S,(cx+r)*S,(cy+r)*S),fill=col,outline=outline,width=width*S)
def dashcircle(cx,cy,r,col):
 for a in range(0,360,12):d.arc(((cx-r)*S,(cy-r)*S,(cx+r)*S,(cy+r)*S),a,a+7,fill=col,width=2*S)
def arrow(a,b,col='#1976b5',width=2):
 line([a,b],col,width);dx=b[0]-a[0];dy=b[1]-a[1];ll=math.hypot(dx,dy);ux=dx/ll;uy=dy/ll
 poly=[b,(b[0]-ux*10-uy*4,b[1]-uy*10+ux*4),(b[0]-ux*10+uy*4,b[1]-uy*10-ux*4)];d.polygon([(x*S,y*S) for x,y in poly],fill=col)
def transform(cx,cy,k,v):return cx+k*v[0],cy-k*v[1]
text(48,28,'花洒剖面与喷水方向核对',34)
text(48,80,'取自最终 FreeCAD 实体：穿过一排 6 个喷水孔的横剖面（X = −1 mm）',21,'#56657a')
text(48,140,'① 真实剖面 + 六路喷水方向',25)
cx,cy,k=385,475,7.25
# Material shading; exact saved-shape section edges are drawn over it.
circle(cx,cy,40*k,'#bdc7d2');circle(cx,cy,38*k,'white');circle(cx,cy,28*k,'#bdc7d2');circle(cx,cy,26*k,'white')
for a in g['axes']:
 m=a['mouth'];u=a['direction'];q=[m[0]-u[0]*4,m[1]-u[1]*4]
 line([transform(cx,cy,k,m),transform(cx,cy,k,q)],'white',1.5*k)
for edge in g['edges']:line([transform(cx,cy,k,v) for v in edge],'#4c5c70',1.1)
dashcircle(cx,cy,26/3*k,'#dc7d21')
for a in g['axes']:
 m=a['mouth'];u=a['direction'];L=-2*(m[0]*u[0]+m[1]*u[1]);end=[m[0]+u[0]*L,m[1]+u[1]*L]
 line([transform(cx,cy,k,m),transform(cx,cy,k,end)],'#3b91bd',1.7)
 for t in [10,33]:
  aa=[m[0]+u[0]*(t-3),m[1]+u[1]*(t-3)];bb=[m[0]+u[0]*t,m[1]+u[1]*t];arrow(transform(cx,cy,k,aa),transform(cx,cy,k,bb),width=2)
 circle(*transform(cx,cy,k,a['tangent']),3,'#dc7d21')
circle(cx,cy,3,'#263449');text(cx+8,cy+8,'O',18)
text(75,794,'灰色：实体壁    白色环带：水腔    蓝线：孔轴向内延长线',18)
text(75,827,'橙色虚线：Ø17.333 mm 切线圆；橙点为六个切点',18,'#ba661a')
line([(754,145),(754,850)],'#d8e0e8',1)
text(800,140,'② 单路相切关系放大',25)
cx,cy,k=1110,425,8
circle(cx,cy,26*k,'white','#8a98a9',2);dashcircle(cx,cy,26/3*k,'#dc7d21')
# Select the mouth on upper-right for a readable normal line.
a=max(g['axes'],key=lambda a:a['mouth'][0]+a['mouth'][1]);m=a['mouth'];u=a['direction'];t=a['tangent'];L=-2*(m[0]*u[0]+m[1]*u[1]);end=[m[0]+u[0]*L,m[1]+u[1]*L]
mp=transform(cx,cy,k,m);tp=transform(cx,cy,k,t);ep=transform(cx,cy,k,end)
arrow(mp,ep,width=3);line([(cx,cy),tp],'#dc7d21',2);line([(cx,cy),mp],'#aab5c2',1)
circle(cx,cy,3,'#263449');circle(*tp,4,'#dc7d21');circle(*mp,4,'#1976b5')
# Right angle marker between the radius and tangent ray.
rvec=[-t[0]/(26/3),-t[1]/(26/3)];q1=[t[0]+rvec[0]*1.5,t[1]+rvec[1]*1.5];q2=[q1[0]+u[0]*1.5,q1[1]+u[1]*1.5];q3=[t[0]+u[0]*1.5,t[1]+u[1]*1.5]
line([transform(cx,cy,k,q1),transform(cx,cy,k,q2),transform(cx,cy,k,q3)],'#ba661a',2)
text(cx-20,cy+12,'O',18);text(tp[0]-18,tp[1]-35,'T',19,'#ba661a');text(mp[0]-15,mp[1]-34,'喷水口',19,'#1976b5')
text(823,670,'内径 D = 52 mm',24)
text(823,710,'切线圆直径 d = D / 3 = 17.333 mm',24,'#ba661a')
text(823,750,'圆心到孔轴距离 OT = 8.6667 mm',24)
text(823,790,'孔轴与 OT 垂直，偏离径向 19.471°',24)
text(823,837,'已从实体孔的圆柱面提取轴线验证，非仅按设定值绘图。',17,'#56657a')
im.resize((1500,900),Image.Resampling.LANCZOS).save(p/'剖面与喷水方向.png')
