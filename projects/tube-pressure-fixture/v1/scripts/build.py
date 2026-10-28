"""Two-piece geometric concept. Dimensions in mm; not a calibrated sensor."""
import sys, json, math
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part
import MeshPart
import importlib.util
round_spec=importlib.util.spec_from_file_location('fixture_round',Path(__file__).resolve().parent/'rounded.py')
rounded=importlib.util.module_from_spec(round_spec);round_spec.loader.exec_module(rounded)

ROOT = Path(__file__).resolve().parents[1]
for name in ('models', 'previews', 'reports', 'print'):
    (ROOT / name).mkdir(exist_ok=True)
V = A.Vector
D = A.newDocument('TubePressureFixture')
D.Label = '管路压力工装'
P = dict(tube_od=3.9, tube_id=2.9, pressure_max_kpa=100,
         length=42.5, width=36.6, base_height=6., upper_height=6.,
         beam_width=8.9, beam_length=9.8, beam_thickness=.8,
         contact_pad_thickness=2.4, flexure_length=7.0,
         gauge_length=8.8, gauge_width=7.5, grid_length=7., grid_width=7., grid_tip_margin=.35, nominal_preload=.10,
         screw_length=6., upper_screw_web=2., pilot_diameter=2.8,
         pilot_depth=4.8, clearance_diameter=3.3,
         channel_width=3.9, sidewall_top=8.4, sidewall_outer_y=4.,
         constrained_length=18.1, contact_width=2.3, contact_length=8.9,
         saddle_radius=1.95, motion_up=0.6, motion_tilt=3., lateral_allowance=.10)
# Keep 0.5 mm longitudinal and 0.7 mm lateral gauge bonding margins.
P['beam_length']=P['gauge_length']+1.0
P['beam_width']=P['gauge_width']+1.4
P['contact_length']=P['beam_width']
P['length']=P['beam_width']+33.6
P['width']=2*(P['beam_length']+8.5)
P['constrained_length']=P['length']-24.4
P['flexure_length']=P['grid_length']
P['flexure_offset']=.5+P['gauge_length']-P['grid_length']-P['grid_tip_margin']
top=P['base_height']+P['upper_height']
post_top=top-P['upper_screw_web']
half_beam=P['beam_width']/2
root_y=-2.5-P['beam_length']
window_y=root_y-1
window_half_x=P['length']/2-12
pad_half_x=P['contact_length']/2
screw_x=P['length']/2-6
screw_y=P['width']/2-6
def box(x,y,z,l,w,h): return Part.makeBox(l,w,h,V(x,y,z))
def tube_cylinder(radius, length=48):
    return Part.makeCylinder(radius,length,V(-length/2,0,6),V(1,0,0))
def bolt(x,y,z,r,h): return Part.makeCylinder(r,h,V(x,y,z))
def add(name,label,shape,color):
    o=D.addObject('PartDesign::Feature',name); o.Label=label; o.Shape=shape
    o.addProperty('App::PropertyColor','DisplayColor'); o.DisplayColor=color
    if A.GuiUp: o.ViewObject.ShapeColor=color
    return o

# Nominal cradle geometry; saddle interference represents elastic preload.
base=box(-P['length']/2,-P['width']/2,0,P['length'],P['width'],6).cut(tube_cylinder(P['tube_od']/2))
# Straight-sided, top-open U channel. Lower semicircle restrains downward
# expansion; vertical sidewalls bound lateral diameter without printable overhangs.
for side in (-1,1):
    wall_y=P['channel_width']/2 if side==1 else -P['sidewall_outer_y']
    base=base.fuse(box(-P['constrained_length']/2,wall_y,5.9,P['constrained_length'],
                       P['sidewall_outer_y']-P['channel_width']/2,
                       P['sidewall_top']-5.9))
upper=box(-P['length']/2,-P['width']/2,6,P['length'],P['width'],P['upper_height']).cut(tube_cylinder(P['tube_od']/2))
upper=upper.cut(box(-window_half_x,window_y,5.9,2*window_half_x,-2*window_y-1,P['upper_height']+.2))
fixed_frame=upper.copy()
# Local flexure under the entire gauge footprint, with thicker end regions.
beam_bottom=top-P['beam_thickness']
pad_bottom=top-P['contact_pad_thickness']
def section(y,halfwidth,bottom):
    pts=[V(-halfwidth,y,bottom),V(halfwidth,y,bottom),V(halfwidth,y,top),V(-halfwidth,y,top)]
    return Part.makePolygon(pts+[pts[0]])
beam=box(-half_beam,root_y,beam_bottom,P['beam_width'],P['beam_length'],P['beam_thickness'])
flex_start=root_y+P['flexure_offset']
flex_end=flex_start+P['flexure_length']
rise=P['contact_pad_thickness']-P['beam_thickness']
P['root_radius']=((flex_start-(window_y-.2))**2+rise**2)/(2*rise)
P['tip_radius']=((-P['contact_width']/2-flex_end)**2+rise**2)/(2*rise)
root_transition=rounded.solid(window_y-.2,pad_bottom,flex_start,beam_bottom,half_beam,top)
tip_transition=rounded.solid(flex_end,beam_bottom,-P['contact_width']/2,pad_bottom,half_beam,top)
# Both the thick end pad and the true tube-contact boss are centered at X=Y=0.
pad=box(-pad_half_x,-P['contact_width']/2,pad_bottom,2*pad_half_x,P['contact_width'],P['contact_pad_thickness'])
saddle_axis_z=6-P['nominal_preload']
contact=box(-P['contact_length']/2,-P['contact_width']/2,saddle_axis_z,
            P['contact_length'],P['contact_width'],pad_bottom-saddle_axis_z+.05)
saddle_cut=Part.makeCylinder(P['saddle_radius'],P['contact_length']+.2,
                             V(-P['contact_length']/2-.1,0,saddle_axis_z),V(1,0,0))
contact=contact.cut(saddle_cut).removeSplitter()
assert contact.isValid() and len(contact.Solids)==1
contact=contact.Solids[0]
upper=upper.fuse(beam).fuse(root_transition).fuse(tip_transition).fuse(pad).fuse(contact).removeSplitter()
for x in (-screw_x,screw_x):
    for y in (-screw_y,screw_y):
        # Base posts meet the underside of the 2 mm upper screw web.
        # This preserves the upper screw web and support-free orientation.
        base=base.fuse(bolt(x,y,5.9,3.2,post_top-5.9))
        base=base.cut(bolt(x,y,post_top-P['pilot_depth'],P['pilot_diameter']/2,P['pilot_depth']+.1))
        upper=upper.cut(bolt(x,y,5.9,3.4,post_top-5.9))
        upper=upper.cut(bolt(x,y,post_top-.1,P['clearance_diameter']/2,P['upper_screw_web']+.2))
base=base.removeSplitter(); upper=upper.removeSplitter()
# Persist native history, and compare it against the established geometry above.
import importlib.util
spec=importlib.util.spec_from_file_location('fixture_history',ROOT/'scripts/history.py')
history=importlib.util.module_from_spec(spec);spec.loader.exec_module(history)
b,u,beam_feature=history.build_history(D,P)
for obj,reference,label,color in [(b,base,'下座',(.25,.5,.65)),
                                (u,upper,'上盖',(.77,.79,.83))]:
    assert obj.Shape.isValid() and len(obj.Shape.Solids)==1
    difference=abs(obj.Shape.Volume-reference.Volume)+abs(obj.Shape.common(reference).Volume-reference.Volume)
    assert difference<1e-6,(obj.Name,difference)
    obj.Label=label
    obj.addProperty('App::PropertyColor','DisplayColor');obj.DisplayColor=color
base=b.Shape;upper=u.Shape
# Exercise real upstream edits and verify propagation through the boolean chain.
original_length=beam_feature.LengthFwd.Value
before=u.Shape.Volume
beam_feature.LengthFwd=original_length+.05;D.recompute()
assert u.Shape.isValid() and abs(u.Shape.Volume-before)>.1
beam_feature.LengthFwd=original_length;D.recompute()
assert abs(u.Shape.Volume-before)<1e-6
sketch=beam_feature.Base
width_index=next(i for i in range(sketch.ConstraintCount) if sketch.Constraints[i].Name=='Width')
sketch.setDatum(width_index,A.Units.Quantity(P['beam_width']+.1));D.recompute()
assert u.Shape.isValid() and abs(u.Shape.Volume-before)>.1
sketch.setDatum(width_index,A.Units.Quantity(P['beam_width']));D.recompute()
assert abs(u.Shape.Volume-before)<1e-6
base=b.Shape;upper=u.Shape
pipe=tube_cylinder(1.95,60).cut(tube_cylinder(1.45,60))
t=add('TubeReference','管道参考',pipe,(.35,.75,.72))
gauge_x=-P['gauge_width']/2
gauge_y=beam.CenterOfMass.y-P['gauge_length']/2
g=add('GaugeReference','应变片参考',
      box(gauge_x,gauge_y,top,P['gauge_width'],P['gauge_length'],.15),(.84,.63,.22))
grid=add('GridReference','敏感栅参考',box(-P['grid_width']/2,flex_start,top+.15,P['grid_width'],P['grid_length'],.02),(.9,.35,.18))
sheet=D.addObject('Spreadsheet::Sheet','Parameters')
sheet.Label='参数记录'
sheet.set('A1','参数'); sheet.set('B1','数值'); sheet.set('C1','单位')
for row,(key,value) in enumerate(P.items(),2):
    sheet.set('A'+str(row),key)
    sheet.set('B'+str(row),str(value))
    sheet.set('C'+str(row),{'pressure_max_kpa':'kPa','motion_tilt':'°'}.get(key,'mm'))
notes=D.addObject('Spreadsheet::Sheet','DesignNotes')
notes.Label='说明'
notes.set('A1','项目');notes.set('B1','说明')
for n,(key,value) in enumerate([
    ('状态','梁厚、材料、硬度、预压、桥路待验证'),
    ('参数表','记录表，不驱动几何；修改脚本后重建，或直接编辑特征属性'),
    ('装配','4×M3×6盘头普通螺丝；头下长6；过盖2、进入底座4；无螺母'),
    ('打印','下座底面朝下；上盖贴片面朝下；0.2mm层厚，实心舌片'),
    ('悬臂','长9.8、宽8.9、厚0.8；两端2.4厚支撑，单圆弧R3.90与R2.31；贴片面平齐'),
    ('采集','敏感栅总区约7×7；焊点朝固定端。暂按栅区距自由侧基底边0.35、距焊点侧边1.45定位；须实物核对，桥路输出待验证'),
    ('约束','管轴X；测量段底弧及左右直壁约束；顶部开放，主要沿+Z变形'),
    ('对中','端块及鞍面中心X=0、Y=0；鞍面中点Z=7.85'),
    ('鞍面','R1.95；沿管轴长8.9，与悬臂同宽；横向宽2.3；与左右壁各有0.80名义间隙'),
    ('预压','未变形鞍面下移0.10；梁上挠与硅胶压缩共同吸收，非指定压紧力'),
    ('运动','触头保守包络：上移0至0.6；绕X轴±3°（枢轴Z12）；X/Y偏移±0.10'),
    ('侧槽','宽3.9名义零间隙；长18.1；侧壁顶高8.4；实际打印配合需验证'),
    ('螺丝','Ø2.8为光孔，不含螺纹；M3普通螺丝需依打印材料试制并验证有效咬合')]):
    notes.set('A'+str(n+2),key);notes.set('B'+str(n+2),value)
sheet.setColumnWidth('A',210);sheet.setColumnWidth('B',110);sheet.setColumnWidth('C',80)
notes.setColumnWidth('A',90);notes.setColumnWidth('B',660)
D.recompute()
checks={'history':{'native_feature_counts':{kind:sum(o.TypeId==kind for o in D.Objects)
         for kind in ('Sketcher::SketchObject','Part::Extrusion','Part::Loft','Part::Cut','Part::MultiFuse')},
         'history_matches_design_geometry':True,'extrusion_edit_propagates':True,'sketch_edit_propagates':True}}
for name,shape in [('lower',base),('upper',upper)]:
    assert shape.isValid() and len(shape.Solids)==1,name
    checks[name]={'valid':shape.isValid(),'solids':len(shape.Solids),'volume_mm3':shape.Volume}
for name,a,c in [('parts',base,upper),('base_tube',base,pipe),('upper_gauge',upper,g.Shape)]:
    vol=a.common(c).Volume; assert vol<1e-6,(name,vol);checks[name+'_intersection_mm3']=vol
checks['contact_gap_mm']=upper.distToShape(pipe)[0]
assert checks['contact_gap_mm']<1e-6
# Entire gauge backing supported on the coplanar skin; thickness varies underneath.
backing_projection=box(gauge_x,gauge_y,top-.1,P['gauge_width'],P['gauge_length'],.1)
assert abs(backing_projection.common(upper).Volume-backing_projection.Volume)<1e-6
checks['gauge_fully_supported']=True
assert abs(flex_start-(gauge_y+P['gauge_length']-P['grid_tip_margin']-P['grid_length']))<1e-7
active_zone=box(-P['grid_width']/2,flex_start,beam_bottom,P['grid_width'],P['grid_length'],P['beam_thickness'])
assert abs(upper.common(active_zone).Volume-active_zone.Volume)<1e-6
under_grid=box(-P['grid_width']/2,flex_start,beam_bottom-.1,P['grid_width'],P['grid_length'],.1)
assert upper.common(under_grid).Volume<1e-6
checks['grid_alignment']={'size_mm':[P['grid_length'],P['grid_width']], 'size_approximate':True,
 'solder_edge_offset_assumed_mm':P['gauge_length']-P['grid_length']-P['grid_tip_margin'],
 'tip_edge_offset_assumed_mm':P['grid_tip_margin'],'solder_side':'fixed end (-Y)',
 'active_area_over_uniform_skin':True,'skin_thickness_mm':P['beam_thickness']}

checks['gauge_backing']={'length_mm':P['gauge_length'],'width_mm':P['gauge_width'],
 'source':'user-confirmed actual backing dimensions',
 'end_margin_each_mm':(P['beam_length']-P['gauge_length'])/2,
 'side_margin_each_mm':(P['beam_width']-P['gauge_width'])/2}
assert abs(contact.CenterOfMass.x)<1e-7 and abs(contact.CenterOfMass.y)<1e-7
assert abs(pad.CenterOfMass.x)<1e-7 and abs(pad.CenterOfMass.y)<1e-7
assert abs(contact.BoundBox.ZMin-(saddle_axis_z+math.sqrt(P['saddle_radius']**2-(P['contact_width']/2)**2)))<1e-7
assert contact.distToShape(pipe)[0]<1e-7
assert contact.common(base).Volume<1e-7
preload_volume=pad.fuse(contact).common(pipe).Volume
assert preload_volume>0
assert abs(upper.common(pipe).Volume-preload_volume)<1e-6
checks['preload']={'nominal_interference_mm':P['nominal_preload'],
 'undeformed_reference_overlap_mm3':preload_volume,
 'meaning':'intended elastic interference; actual compression, beam deflection and force uncalculated'}
# Conservative continuous motion envelope, not just sampled poses.
# For rotation about X through (0,0,top), |delta y| <= |top-z| sin(theta).
# The z lower bound deliberately omits the upward cos(theta) contribution.
# Bounding boxes cover ALL translations and tilts within the stated limits.
theta=math.radians(P['motion_tilt'])
envelopes=[]
for solid in (contact,pad):
    bb=solid.BoundBox
    ymax=max(abs(bb.YMin),abs(bb.YMax))
    reach=max(abs(top-bb.ZMin),abs(top-bb.ZMax))
    half_y=ymax+reach*math.sin(theta)+P['lateral_allowance']
    zlo=bb.ZMin-ymax*math.sin(theta)
    zhi=top+ymax*math.sin(theta)+P['motion_up']
    envelope=box(bb.XMin-P['lateral_allowance'],-half_y,zlo,
                 bb.XLength+2*P['lateral_allowance'],2*half_y,zhi-zlo)
    assert envelope.common(base).Volume<1e-7
    assert envelope.common(fixed_frame).Volume<1e-7
    envelopes.append(envelope)
min_base_gap=min(s.distToShape(base)[0] for s in envelopes)
assert min_base_gap>.45
checks['saddle_motion']={'length_mm':P['contact_length'],'width_mm':P['contact_width'],
 'radius_mm':P['saddle_radius'],'nominal_side_gap_mm':(P['channel_width']-P['contact_width'])/2,
 'upward_translation_range_mm':[0,P['motion_up']], 'tilt_about_x_degrees':[-P['motion_tilt'],P['motion_tilt']],
 'pivot_xyz_mm':[0,0,top], 'xy_translation_allowance_mm':P['lateral_allowance'],
 'conservative_continuous_envelope_base_clearance_mm':min_base_gap,
 'base_and_fixed_frame_collision':False,
 'scope':'rigid contact/pad envelope only; flexure stress, nonlinear deformation and manufacturing tolerances unvalidated'}
# The tube center section must touch the bottom and both side constraints.
for y,z in [(0,4.05),(-1.95,6),(1.95,6)]:
    assert base.distToShape(Part.Vertex(V(0,y,z)))[0]<1e-7
# A hypothetical lateral displacement penetrates a wall. Upward swept volume
# of the tube does not intersect the lower cradle (not a material simulation).
side_intersections=[]
for dy in (-.05,.05):
    shifted=pipe.copy();shifted.translate(V(0,dy,0))
    volume=base.common(shifted).Volume;assert volume>1e-4;side_intersections.append(volume)
lifted=pipe.copy();lifted.translate(V(0,0,.2))
assert base.common(lifted).Volume<1e-6
checks['constraint']={'contact_center_xy_mm':[0,0],'pad_center_xy_mm':[0,0],
 'u_channel_width_mm':3.9,'sidewall_top_mm':P['sidewall_top'],
 'side_shift_005mm_intersection_mm3':side_intersections,
 'upward_02mm_base_intersection_mm3':base.common(lifted).Volume,
 'scope':'geometric restraint only; axial slip, silicone deformation, printed clearances unvalidated'}
checks['flexure']={'length_mm':P['beam_length'],'width_mm':P['beam_width'],'thickness_mm':P['beam_thickness'],
                   'active_flexure_length_mm':P['flexure_length'],'offset_from_beam_root_mm':P['flexure_offset'],'root_radius_mm':P['root_radius'],
                   'pad_thickness_mm':P['contact_pad_thickness'],'stiffness_per_unit_length_pad_over_flexure':2*pad_half_x*P['contact_pad_thickness']**3/(P['beam_width']*P['beam_thickness']**3),
                   'mechanical_validation':'geometric only; no FEA or pressure calibration'}
checks['screw']={'assumption':'M3 machine screw, pan head, 6mm under-head length; smooth 2.8mm base holes, thread engagement unverified',
                 'upper_web_mm':2.,'penetration_including_tip_mm':4.,
                 'pilot_depth_mm':4.8,'tip_clearance_mm':.8}
# Check shank clearance through upper, pilot channel, and seating at each post.
for x in (-screw_x,screw_x):
    for y in (-screw_y,screw_y):
        assert upper.common(bolt(x,y,post_top,1.5,P['upper_screw_web'])).Volume<1e-6
        assert base.common(bolt(x,y,post_top-P['pilot_depth']+.01,P['pilot_diameter']/2-.01,P['pilot_depth'])).Volume<1e-6
        assert upper.distToShape(bolt(x,y,post_top-.001,3.2,.001))[0]<1e-6
spec=importlib.util.spec_from_file_location('fixture_naming',ROOT/'scripts/naming.py')
naming=importlib.util.module_from_spec(spec);spec.loader.exec_module(naming)
naming.apply(D)
# Historical geometry volumes recorded on 2026-10-27 before 17:27.
assert abs(base.Volume-9653.747621737159)<1e-6
assert abs(upper.Volume-5891.687307734708)<1e-6
checks['historical_volume_match']=True
D.saveAs(str(ROOT/'models/管路压力工装.FCStd'))
Part.export([b,u],str(ROOT/'models/管路压力工装_两件.step'))
Part.export([b],str(ROOT/'models/下座.step'))
Part.export([u],str(ROOT/'models/上盖_一体悬臂.step'))
print_upper=upper.copy()
print_upper.rotate(V(),V(1,0,0),180)
print_upper.translate(V(0,0,top))
for name,shape in [('下座_底面朝下',base),('上盖_贴片面朝下',print_upper)]:
    assert abs(shape.BoundBox.ZMin)<1e-7
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.03,AngularDeflection=.12,Relative=False)
    assert mesh.isSolid()
    mesh.write(str(ROOT/'print'/(name+'.stl')))
    # Compare sampled horizontal slices at a 0.2 mm layer interval.
    # A nested footprint cannot start an unsupported island or overhang.
    previous=None;max_new=0.
    for i in range(round(shape.BoundBox.ZMax/.2)):
        z=.1+.2*i
        sample=shape.common(box(-30,-30,z,60,60,.002))
        sample.translate(V(0,0,-z))
        if previous is not None:max_new=max(max_new,sample.cut(previous).Volume/.002)
        previous=sample
    assert max_new<1e-5,(name,max_new)
    checks[name]={'mesh_closed':True,'bed_z_mm':shape.BoundBox.ZMin,'sampled_unsupported_area_mm2':max_new}
(ROOT/'reports/geometry.json').write_text(json.dumps(checks,indent=2))

# Tessellated CAD preview, with an exploded upper part for assembly clarity.
def projected(v):
    x,y,z=v
    return (530+7.5*(.84*x-.54*y),520+7.5*(.30*x+.47*y-.83*z))
polygons=[]
render_data=[]
for shape,color,offset in [(base,'#598ca7',0),(pipe,'#60b6ae',0),(upper,'#bec8d6',20),(g.Shape,'#dfb553',20)]:
    vertices,triangles=shape.tessellate(.12)
    for tri in triangles:
        vv=[(vertices[i].x,vertices[i].y,vertices[i].z+offset) for i in tri]
        normal=(vertices[tri[1]]-vertices[tri[0]]).cross(vertices[tri[2]]-vertices[tri[0]])
        shade=.55+.45*abs(normal.z)/max(normal.Length,1e-12)
        shaded='#'+''.join('%02x'%int(int(color[j:j+2],16)*shade) for j in (1,3,5))
        render_data.append({'points':[[*projected(v),.45*v[0]+.7*v[1]+.56*v[2]] for v in vv], 'color':shaded})
        depth=sum(-.45*x-.7*y-.56*z for x,y,z in vv)/3
        points=' '.join('%.2f,%.2f'%projected(v) for v in vv)
        polygons.append((depth,f'<polygon points="{points}" fill="{color}" stroke="{color}" stroke-width="0.4"/>'))
polygons.sort(reverse=True,key=lambda a:a[0])
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="740" viewBox="0 0 1060 740"><rect width="1060" height="740" fill="#f5f7fa"/>'
svg+='<g font-family="Arial,sans-serif" fill="#24394a"><text x="40" y="48" font-size="26">Two-piece silicone tube pressure fixture</text><text x="40" y="80" font-size="17">0-100 kPa  |  tube OD 3.9 / ID 2.9 mm</text></g>'
svg+=''.join(p[1] for p in polygons)
svg+='<g font-family="Arial,sans-serif" font-size="17" fill="#24394a"><text x="40" y="645">Upper: print with gauge face DOWN; lower: flat bottom DOWN</text><text x="40" y="673">Flexure 0.8 mm | arcs R3.90 / R2.31 mm | total height 12 mm</text><text x="40" y="701">42.5 x 36.6 mm | 4 x M3x6 machine screws | 2 mm web + 4 mm penetration</text></g></svg>'
(ROOT/'previews/exploded.svg').write_text(svg)
(ROOT/'reports/triangles.json').write_text(json.dumps(render_data))
# True X=0 assembly section, perpendicular to the tube. No exploded offsets.
section_render=[]
for shape,color in [(base,'#598ca7'),(pipe,'#60b6ae'),(upper,'#bec8d6'),(g.Shape,'#dfb553')]:
    sliced=shape.common(box(-.025,-25,-1,.05,50,20))
    vertices,triangles=sliced.tessellate(.03)
    for tri in triangles:
        section_render.append({'points':[[530+20*vertices[i].y,570-20*vertices[i].z,vertices[i].x] for i in tri], 'color':color})
(ROOT/'reports/section_triangles.json').write_text(json.dumps(section_render))
print(json.dumps(checks,indent=2))
if A.GuiUp:
    import importlib.util
    spec=importlib.util.spec_from_file_location('fixture_final_view',ROOT/'scripts/final_view.py')
    presentation=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(presentation)
    presentation.apply(D)
else:
    print('Geometry saved. Run scripts/final_view.py in FreeCAD GUI to finalize visibility and camera.')
