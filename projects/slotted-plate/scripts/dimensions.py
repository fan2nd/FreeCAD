from pathlib import Path
from html import escape
import ast, json, math
root=Path(__file__).resolve().parents[1]
module=ast.parse((root/'scripts'/'build.py').read_text())
rows=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rows' for t in n.targets))
confirmed=json.loads((root/'scripts'/'measurements.json').read_text())['confirmed']
values={k:confirmed.get(k,v) for k,n,v in rows}
values.update(B3=values['B1']/2*(1+1/math.sin(math.radians(values['D1']/2))),C8=values['A6']-values['B1']/2+values['C7'],C4=values['B1']/2+.3,C6=values['P1'])
values.update(H8=values['H9']+.6,H11=values['C3']-values['H7'])
values['C2']=sum(values[k] for k in ('P1','B2','B5','B7','B9','A5','A2'))-values['C9']
rows=[(k,'笔截面横向总宽' if k=='B3' else n,values[k]) for k,n,v in rows]

s=['<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1640" viewBox="0 0 1800 1640"><defs><marker id="a" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto-start-reverse"><path d="M7,0 L0,3.5 L7,7" fill="none" stroke="#19759c"/></marker></defs><rect width="1800" height="1640" fill="white"/><style>text{font-family:"PingFang SC","Arial",sans-serif;fill:#182e3e} .shape{stroke:#263a46;stroke-width:2.5;fill:#eff4f7} .dim{stroke:#19759c;stroke-width:1.4;fill:none} .ext{stroke:#87a3b3;stroke-width:1;fill:none}</style>']
def text(x,y,t,size=21):s.append(f'<text x="{x}" y="{y}" font-size="{size}">{escape(t)}</text>')
def line(x1,y1,x2,y2,cls='ext'):s.append(f'<path d="M{x1},{y1} L{x2},{y2}" class="{cls}"/>')
def dim(x1,y1,x2,y2,t):
 s.append(f'<path d="M{x1},{y1} L{x2},{y2}" class="dim" marker-start="url(#a)" marker-end="url(#a)"/>');text((x1+x2)/2+8,(y1+y2)/2-9,t,19)
def path(d):s.append(f'<path d="{d}" class="shape"/>')
def circle(x,y):s.append(f'<circle cx="{x}" cy="{y}" r="7" fill="white" stroke="#263a46" stroke-width="2.5"/>')
text(55,55,'推力计与笔 · 尺寸补全图',36);text(55,96,'长度 mm / 角度 deg ｜ ✓ 已确认；≈ 推导；? 未确认占位 ｜ 尖角朝侧向，圆弧侧沉入',23)
text(100,150,'① 底板俯视：左侧固定推力计，右侧嵌放笔',25)
path('M140 220 H1140 V450 H140 Z')
for x in (215,395):
 for y in (280,385):circle(x,y)
s.append('<path d="M505 220 V450" class="ext" stroke-dasharray="8,5"/>')
path('M640 312 H1060 V358 H640 Z')
text(245,420,'推力计安装区',19);text(745,400,'笔的圆弧盲槽',19)
dim(140,190,1140,190,'C2');dim(110,220,110,450,'C1');dim(215,260,395,260,'H3');dim(425,280,425,385,'H2');dim(140,480,215,480,'H4−C9');dim(640,480,1060,480,'C5');dim(1060,510,1140,510,'C6');text(570,540,'底面4×沉孔：⌀7.3 深2；螺丝处保留6，杯头突出1.6',19)
text(1250,150,'② 笔轴向截面 / 入槽',25)
path('M1260 395 H1300 V382.4 H1380 Q1410 398 1440 382.4 H1650 V395 H1695 V495 H1260 Z')
path('M1446.53 282.4 A60 60 0 1 0 1446.53 377.6 L1508.57 330 Z')
line(1240,382.4,1730,382.4,'dim');text(1550,365,'槽区表面',19)
dim(1350,240,1508.57,240,'B3');dim(1560,270,1560,390,'B1');dim(1610,382.4,1610,390,'C7');text(1530,430,'沉入 1.41',19)
text(1515,310,'D1 = 75°',20);text(1290,535,'C4 槽圆弧；C8 抬高 2.31',20)
text(100,605,'③ 推力计底视与笔顶视（端部相向）',25)
path('M145 690 H470 V890 H145 Z');path('M470 767 H530 V813 H470 Z')
for x in (210,390):
 for y in (735,845):circle(x,y)
text(170,922,'底部 4 × ⌀H6，深 H5',20)
dim(145,660,470,660,'A2');dim(115,690,115,890,'A1');dim(470,855,530,855,'A5');text(480,744,'⌀A4',19)
# Pen lies with T head left, tail right.
path('M590 768 H608 V782 H650 V735 H710 V710 H1200 V748 H1250 V832 H1200 V870 H710 V845 H650 V798 H608 V812 H590 Z')
dim(710,680,1200,680,'B2');dim(1290,710,1290,870,'B1');dim(1200,920,1250,920,'B11');text(1240,735,'⌀B10',19)
dim(650,925,710,925,'B5');text(635,704,'⌀B4',19);dim(608,960,650,960,'B7');text(595,855,'⌀B6',19);text(555,730,'⌀B8',19);text(545,895,'B9 头厚',19)
text(1400,655,'④ 测力轴高度',23);path('M1405 710 H1630 V840 H1405 Z');path('M1630 778 H1700 V812 H1630 Z');line(1380,840,1730,840,'dim');line(1600,795,1730,795);dim(1730,795,1730,840,'A6');text(1405,885,'A3：机身厚度',20);text(1405,925,'A6：轴心距机底',20)
line(55,1000,1745,1000);text(55,1043,'尺寸状态（未确认项仍需补填）',25)
# Three columns of ten entries, all values sourced from the model build script.
for i,(key,name,value) in enumerate(rows):
 col=i//14;row=i%14;x=55+col*580;y=1080+row*32
 text(x,y,f'{key}  {name}',19);mark='✓' if key in confirmed else ('≈' if key in ('B3','C2','C4','C6','C8','C9','P1','H8','H11') else '?');text(x+330,y,f'{mark} {value:.2f}'+('  ______' if mark=='?' else ''),19)
text(55,1570,'测量提示：H2 横向孔距，H3 沿笔轴方向孔距；H4 从推力计外端边量至近排孔中心。',19)
text(55,1610,'底板两端收短至233×70；推力计端悬出C9=10.4，外排孔距板端7。适配256×256打印平台。',19)
s.append('</svg>');(root/'previews'/'dimensions.svg').write_text('\n'.join(s))
# Render PNG when invoked inside FreeCAD's GUI Python environment.
try:
 from PySide import QtSvg, QtGui, QtWidgets
 if QtWidgets.QApplication.instance():
  renderer=QtSvg.QSvgRenderer(str(root/'previews'/'dimensions.svg'))
  image=QtGui.QImage(1800,1640,QtGui.QImage.Format_ARGB32);image.fill(0xffffffff)
  painter=QtGui.QPainter(image);renderer.render(painter);painter.end()
  image.save(str(root/'previews'/'dimensions.png'))
except ImportError:
 pass
