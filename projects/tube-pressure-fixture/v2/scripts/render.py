import json, math, os
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtGui import QGuiApplication,QImage,QPainter,QColor,QFont,QPen
from PySide6.QtCore import Qt
root=Path(__file__).resolve().parents[1]
app=QGuiApplication([])
w,h=1060,740
def raster(filename):
    im=QImage(w,h,QImage.Format_RGB32); im.fill(QColor('#f5f7fa'))
    depth=[-1e30]*(w*h)
    for t in json.loads((root/'reports'/filename).read_text()):
        (ax,ay,az),(bx,by,bz),(cx,cy,cz)=t['points']
        den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den)<1e-9:continue
        col=QColor(t['color']).rgb()
        for y in range(max(0,math.floor(min(ay,by,cy))),min(h,math.ceil(max(ay,by,cy))+1)):
            for x in range(max(0,math.floor(min(ax,bx,cx))),min(w,math.ceil(max(ax,bx,cx))+1)):
                a=((by-cy)*(x+.5-cx)+(cx-bx)*(y+.5-cy))/den
                b=((cy-ay)*(x+.5-cx)+(ax-cx)*(y+.5-cy))/den
                c=1-a-b
                if min(a,b,c)<-1e-8:continue
                z=a*az+b*bz+c*cz;i=y*w+x
                if z>depth[i]:depth[i]=z;im.setPixel(x,y,col)
    return im
im=raster('triangles.json')
p=QPainter(im);p.setPen(QColor('#24394a'));p.setFont(QFont('Helvetica',24))
p.drawText(40,48,'管路压力工装')
p.setFont(QFont('Helvetica',13))
for x,y,text in [(40,80,'0–100 kPa｜硅胶管外径 3.9 / 内径 2.9 mm｜3EB 基底 8.8 × 7.5 mm'),(40,645,'居中鞍面 R1.95，长8.9、宽2.3；名义预压0.20；两侧各留0.80间隙。'),(40,673,'悬臂厚0.6（3层），根部单圆弧R3.66；自由端同厚；装配总高8.4。'),(40,701,'预压由硅胶压缩与薄梁上挠共同吸收；未计算实际压紧力或标定量程。')]:p.drawText(x,y,text)
p.end();assert im.save(str(root/'previews/exploded.png'))
im=raster('section_triangles.json')
p=QPainter(im);p.setRenderHint(QPainter.Antialiasing)
p.setPen(QColor('#24394a'));p.setFont(QFont('Helvetica',24))
p.drawText(40,48,'管道中心装配剖面 · 底部与左右约束')
p.setFont(QFont('Helvetica',13))
p.drawText(40,80,'X=0未变形几何剖面；鞍面与管道的名义重叠用于预压；单位 mm')
p.drawText(70,205,'黄色：3EB 基底')
p.drawLine(280,215,365,400)
p.drawText(300,395,'柔性段：长7 / 厚0.6')
p.drawLine(380,382,380,412)
p.drawText(160,275,'根部圆弧R3.66')
p.drawLine(290,282,290,421)
p.drawText(570,240,'R1.95 鞍面中心 = 管道中心线')
p.drawLine(575,248,530,415)
p.drawText(615,435,'槽宽3.9，悬臂侧局部降至7.2')
p.drawLine(610,443,576,443)
p.drawText(615,471,'底部圆弧：R1.95')
p.drawLine(610,478,547,489)
p.setPen(QPen(QColor('#b55343'),1,Qt.DashLine));p.drawLine(530,260,530,570)
p.setPen(QPen(QColor('#b55343'),2))
def arrow(x1,y1,x2,y2):
    p.drawLine(x1,y1,x2,y2)
    a=math.atan2(y2-y1,x2-x1)
    for d in (-.5,.5):p.drawLine(x2,y2,round(x2-9*math.cos(a+d)),round(y2-9*math.sin(a+d)))
arrow(480,458,490,458);arrow(580,458,570,458);arrow(530,520,530,491)
arrow(570,355,570,300)
p.setPen(QColor('#24394a'));p.drawText(585,315,'向上推动舌片')
p.drawText(40,645,'鞍面宽2.3，两侧各留0.80；鞍面比名义管顶下移0.20形成预压。')
p.drawText(40,673,'运动校核：上移0～0.6、绕X轴±3°、X/Y偏移±0.10的保守包络。')
p.drawText(40,701,'包络与底座净距大于0.45；此为几何校核，不代表材料允许行程。')
p.end();assert im.save(str(root/'previews/section.png'))
