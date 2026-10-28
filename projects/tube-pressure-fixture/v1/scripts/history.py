"""Native, editable sketch/extrusion/loft/boolean history; no shape snapshots."""
import FreeCAD as A
import Part, Sketcher
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location("fixture_round",Path(__file__).with_name("rounded.py"))
rounded=importlib.util.module_from_spec(spec);spec.loader.exec_module(rounded)
V=A.Vector

def build_history(D,P):
    top=P['base_height']+P['upper_height']
    post_top=top-P['upper_screw_web']
    def obj(kind,name,label):
        o=D.addObject(kind,name);o.Label=label
        return o
    def rectangle(name,x,y,z,w,h,rotation=None):
        s=obj('Sketcher::SketchObject',name,name+' · 矩形草图')
        s.Placement=A.Placement(V(x,y,z),rotation or A.Rotation())
        pts=[V(0,0,0),V(w,0,0),V(w,h,0),V(0,h,0)]
        for i in range(4):s.addGeometry(Part.LineSegment(pts[i],pts[(i+1)%4]),False)
        for i in range(4):s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%4,1))
        for i in (0,2):s.addConstraint(Sketcher.Constraint('Horizontal',i))
        for i in (1,3):s.addConstraint(Sketcher.Constraint('Vertical',i))
        s.addConstraint(Sketcher.Constraint('Coincident',0,1,-1,1))
        a=s.addConstraint(Sketcher.Constraint('Distance',0,w));s.renameConstraint(a,'Width')
        a=s.addConstraint(Sketcher.Constraint('Distance',1,h));s.renameConstraint(a,'Height')
        return s
    def extrude(name,s,length,direction=V(0,0,1)):
        e=obj('Part::Extrusion',name,name+' · 拉伸')
        e.Base=s;e.DirMode='Custom';e.Dir=direction;e.LengthFwd=length;e.Solid=True
        return e
    def block(name,x,y,z,w,h,t):return extrude(name,rectangle(name+'Sketch',x,y,z,w,h),t)
    def cylinder(name,x,y,z,r,h,axis=V(0,0,1)):
        s=obj('Sketcher::SketchObject',name+'Sketch',name+' · 圆草图')
        s.Placement=A.Placement(V(x,y,z),A.Rotation(V(0,0,1),axis))
        s.addGeometry(Part.Circle(V(),V(0,0,1),r),False)
        s.addConstraint(Sketcher.Constraint('Coincident',0,3,-1,1))
        a=s.addConstraint(Sketcher.Constraint('Radius',0,r));s.renameConstraint(a,'Radius')
        return extrude(name,s,h,axis)
    def cut(name,a,b):
        o=obj('Part::Cut',name,name+' · 切除');o.Base=a;o.Tool=b;o.Refine=True;return o
    def fuse(name,parts):
        o=obj('Part::MultiFuse',name,name+' · 合并');o.Shapes=parts;o.Refine=True;return o
    def ramp(name,y1,w1,z1,y2,w2,z2):
        assert abs(w1-w2)<1e-7
        s=obj('Sketcher::SketchObject',name+'Sketch',name)
        s.Placement=rounded.placement(w1)
        for geo in rounded.profile(y1,z1,y2,z2,top):
            i=s.addGeometry(geo,False)
            # Fix the exact tangent construction; source dimensions live in P.
            s.addConstraint(Sketcher.Constraint('Block',i))
        return extrude(name,s,2*w1,V(1,0,0))
    L,W=P['length'],P['width'];sx=L/2-6;sy=W/2-6
    blank=block('BaseBlank',-L/2,-W/2,0,L,W,6)
    groove=cylinder('BaseTubeTool',-24,0,6,P['tube_od']/2,48,V(1,0,0))
    base=cut('BaseGroove',blank,groove)
    walls=[]
    for i,y in enumerate((-P['sidewall_outer_y'],P['channel_width']/2)):
        walls.append(block('SideWall'+str(i),-P['constrained_length']/2,y,5.9,P['constrained_length'],P['sidewall_outer_y']-P['channel_width']/2,P['sidewall_top']-5.9))
    base=fuse('BaseWalls',[base]+walls)
    posts=[];holes=[]
    for i,(x,y) in enumerate(( (x,y) for x in (-sx,sx) for y in (-sy,sy))):
        posts.append(cylinder('Post'+str(i),x,y,5.9,3.2,post_top-5.9))
        holes.append(cylinder('Pilot'+str(i),x,y,post_top-P['pilot_depth'],P['pilot_diameter']/2,P['pilot_depth']+.1))
    base=fuse('BasePosts',[base]+posts)
    for i,h in enumerate(holes):base=cut('Lower' if i==3 else 'PilotCut'+str(i),base,h)
    blank=block('CoverBlank',-L/2,-W/2,6,L,W,P['upper_height'])
    groove=cylinder('CoverTubeTool',-24,0,6,P['tube_od']/2,48,V(1,0,0))
    upper=cut('CoverGroove',blank,groove)
    root=-2.5-P['beam_length'];wy=root-1;wx=L/2-12
    window=block('WindowTool',-wx,wy,5.9,2*wx,-2*wy-1,P['upper_height']+.2)
    upper=cut('CoverWindow',upper,window)
    half=P['beam_width']/2;ph=P['contact_length']/2;bb=top-P['beam_thickness'];pb=top-P['contact_pad_thickness']
    beam=block('Flexure',-half,root,bb,P['beam_width'],P['beam_length'],P['beam_thickness'])
    start=root+P['flexure_offset'];end=start+P['flexure_length']
    r=ramp('RootRamp',wy-.2,half,pb,start,half,bb)
    t=ramp('TipRamp',end,half,bb,-P['contact_width']/2,half,pb)
    pad=block('ContactPad',-ph,-P['contact_width']/2,pb,2*ph,P['contact_width'],P['contact_pad_thickness'])
    z=6-P['nominal_preload'];cl=P['contact_length'];cw=P['contact_width']
    contact=block('ContactBlank',-cl/2,-cw/2,z,cl,cw,pb-z+.05)
    tool=cylinder('SaddleTool',-cl/2-.1,0,z,P['saddle_radius'],cl+.2,V(1,0,0))
    contact=cut('SaddleContact',contact,tool)
    upper=fuse('CoverFlexure',[upper,r,beam,t,pad,contact])
    for i,(x,y) in enumerate(( (x,y) for x in (-sx,sx) for y in (-sy,sy))):
        relief=cylinder('PostRelief'+str(i),x,y,5.9,3.4,post_top-5.9)
        upper=cut('ReliefCut'+str(i),upper,relief)
        hole=cylinder('ScrewClearance'+str(i),x,y,post_top-.1,P['clearance_diameter']/2,P['upper_screw_web']+.2)
        upper=cut('Upper' if i==3 else 'ClearanceCut'+str(i),upper,hole)
    D.recompute()
    return base,upper,beam
