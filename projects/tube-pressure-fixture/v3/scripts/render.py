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
for mode,title in [('assembly','v3 · 装配'),('exploded','v3 · 三件分解'),('section','v3 · 管道中心剖面')]:
    im=raster(mode+'.json')
    painter=QPainter(im);painter.setPen(QColor('#24394a'));painter.setFont(QFont('Helvetica',24));painter.drawText(40,48,title)
    painter.setFont(QFont('Helvetica',13))
    for x,y,text in [(40,80,'蓝：下座   灰：上盖   黄：独立形变板   绿：管道参考'),(40,645,'圆弧缺口 R1.95 对准管道；顶端最薄 0.6 mm，两侧厚 2.2 mm。'),(40,673,'上盖两端限位，形变板槽间隙 0.3 mm；名义预压 0.15 mm。'),(40,701,'0.2 mm 层高；形变板平面朝下打印；几何验证不替代强度与压力标定。')]:painter.drawText(x,y,text)
    painter.end();assert im.save(str(root/'previews'/(mode+'.png')))
