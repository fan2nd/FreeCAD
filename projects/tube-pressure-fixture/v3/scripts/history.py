"""Native, editable sketch/extrusion/loft/boolean history; no shape snapshots."""
import FreeCAD as A
import Part, Sketcher
V=A.Vector

def build_history(D,P):
    top=P['plate_top']
    post_top=P['base_height']+P['upper_height']-P['upper_screw_web']
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
    L,W=P['length'],P['width'];sx=L/2-6;sy=W/2-6
    blank=block('BaseBlank',-L/2,-W/2,0,L,W,6)
    groove=cylinder('BaseTubeTool',-24,0,6,P['tube_od']/2,48,V(1,0,0))
    base=cut('BaseGroove',blank,groove)
    walls=[]
    for i,y in enumerate((-4.,1.95)):
        wall=block('SideWall'+str(i),-P['wall_length']/2,y,5.9,P['wall_length'],2.05,2.5)
        tool=block('WallReliefTool'+str(i),-P['wall_relief_length']/2,y-.1,P['wall_local_top'],P['wall_relief_length'],2.25,8.5-P['wall_local_top'])
        walls.append(cut('WallRelief'+str(i),wall,tool))
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
    window=block('WindowTool',-P['window_half_x'],-P['window_half_y'],5.9,2*P['window_half_x'],2*P['window_half_y'],P['upper_height']+.2)
    upper=cut('CoverWindow',upper,window)
    pocket=block('PlatePocketTool',-P['plate_width']/2-P['fit_gap'],-P['plate_length']/2-P['fit_gap'],5.9,P['plate_width']+2*P['fit_gap'],P['plate_length']+2*P['fit_gap'],top-5.9)
    upper=cut('PlatePocket',upper,pocket)
    for i,(x,y) in enumerate(( (x,y) for x in (-sx,sx) for y in (-sy,sy))):
        relief=cylinder('PostRelief'+str(i),x,y,5.9,3.4,post_top-5.9)
        upper=cut('ReliefCut'+str(i),upper,relief)
        hole=cylinder('ScrewClearance'+str(i),x,y,post_top-.1,P['clearance_diameter']/2,P['upper_screw_web']+.2)
        upper=cut('Upper' if i==3 else 'ClearanceCut'+str(i),upper,hole)
    half=P['plate_width']/2; length=P['plate_length']/2
    beam=block('PlateBlank',-half,-length,top-P['end_thickness'],2*half,2*length,P['end_thickness'])
    notch=cylinder('NotchTool',-half-.1,0,P['notch_axis_z'],P['notch_radius'],2*half+.2,V(1,0,0))
    plate=cut('Plate',beam,notch)
    D.recompute()
    labels={'BaseBlank':'底板','BaseGroove':'管槽','BaseWalls':'侧壁','BasePosts':'螺丝柱','CoverBlank':'盖板','CoverGroove':'压管槽','CoverWindow':'开窗','PlatePocket':'限位槽','PlateBlank':'板坯','NotchTool':'管道缺口','PlateEnd0':'端板1','PlateEnd1':'端板2','Transition0':'圆弧1','Transition1':'圆弧2','Lower':'下座','Upper':'上盖','Plate':'形变板'}
    prefixes={'SideWall':'侧壁','WallReliefTool':'侧壁避让','WallRelief':'避让','PostRelief':'柱槽','ReliefCut':'柱槽切除','ScrewClearance':'螺丝孔','ClearanceCut':'螺孔切除','PilotCut':'底孔切除','Pilot':'底孔','Post':'螺丝柱','BaseTubeTool':'管槽轮廓','CoverTubeTool':'压管轮廓','WindowTool':'开窗轮廓','PlatePocketTool':'限位轮廓'}
    for o in D.Objects:
        raw=o.Name.removesuffix('Sketch')
        for prefix in sorted(prefixes,key=len,reverse=True):
            if raw.startswith(prefix):
                labels[raw]=prefixes[prefix]+raw[len(prefix):];break
        name=o.Name
        if name.endswith('Sketch'):
            o.Label=labels.get(name[:-6],name[:-6])+'草图'
        else:o.Label=labels.get(name,name)
    return base,upper,plate,beam
