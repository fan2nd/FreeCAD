import sys,os
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A,MeshPart
from pathlib import Path
os.environ['MPLCONFIGDIR']='/private/tmp/screen_stand_mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import LightSource
BASE=Path(__file__).resolve().parents[1]
MODELS=BASE/'models'; PRINT=BASE/'print'; PREVIEWS=BASE/'previews'; REPORTS=BASE/'reports'
for directory in (MODELS,PRINT,PREVIEWS,REPORTS): directory.mkdir(parents=True,exist_ok=True)
d=A.openDocument(str(MODELS/'L型底座_中间四孔_屏幕落底.FCStd'))
fig=plt.figure(figsize=(12,7),facecolor='white')
for j,az in [(1,0),(2,180)]:
 ax=fig.add_subplot(1,2,j,projection='3d');fsall=[];cs=[]
 for name in ['PrintableStand','PCB','ScreenEnvelope','EthernetEnvelope','USBDataEnvelope','USBPowerEnvelope']:
  o=d.getObject(name);m=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.08,AngularDeflection=.15,Relative=False)
  vs,fs=m.Topology;v=np.array([[a.x,a.y,a.z] for a in vs]);faces=v[np.array(fs)]
  fsall.extend(faces);cs.extend([tuple(o.PreviewColor[:3])]*len(faces))
 ax.add_collection3d(Poly3DCollection(fsall,facecolors=cs,linewidths=0,antialiased=False,shade=True,lightsource=LightSource(azdeg=0,altdeg=50)))
 ax.set(xlim=(-40,40),ylim=(-18,86),zlim=(0,140));ax.set_box_aspect((80,104,140));ax.set_proj_type('ortho');ax.view_init(elev=0,azim=az);ax.set_axis_off();ax.set_title('SIDE' if j==1 else 'OPPOSITE SIDE')
fig.subplots_adjust(0,0,1,.95,0,0);fig.savefig(PREVIEWS/'side_preview.png',dpi=160)
