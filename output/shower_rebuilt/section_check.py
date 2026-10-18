import sys,json,math
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part
V=App.Vector;p=Path(__file__).parent;d=App.openDocument(str(p.parent.parent/'按摩花洒_G12_高50_斜喷水.FCStd'));s=d.ShowerFinished.Shape
section=s.section(Part.Face(Part.makePolygon([V(-1,-70,-70),V(-1,70,-70),V(-1,70,70),V(-1,-70,70),V(-1,-70,-70)])))
assert len(section.Edges)>12
edges=[]
for e in section.Edges:
 points=e.discretize(Deflection=.02)
 edges.append([[v.y,v.z] for v in points])
# Read the actual cylindrical nozzle faces from the saved solid.
axes=[]
for f in s.Faces:
 surf=f.Surface
 if isinstance(surf,Part.Cylinder) and abs(surf.Radius-.75)<1e-6:
  c=surf.Center;a=surf.Axis
  if abs(c.x+1)<1e-5:
   # Intersect the bore axis with the inner cylinder r=26; choose nearest mouth.
   dot=c.y*a.y+c.z*a.z
   roots=[-dot+math.sqrt(dot*dot-(c.y*c.y+c.z*c.z-26**2)),-dot-math.sqrt(dot*dot-(c.y*c.y+c.z*c.z-26**2))]
   candidates=[c+a*t for t in roots];mouth=min(candidates,key=lambda v:(v-f.CenterOfMass).Length)
   if mouth.y*a.y+mouth.z*a.z>0:a=-a
   t=-(mouth.y*a.y+mouth.z*a.z)
   foot=mouth+a*t;distance=math.hypot(foot.y,foot.z)
   axes.append({'mouth':[mouth.y,mouth.z],'direction':[a.y,a.z],'tangent':[foot.y,foot.z],'distance_to_center':distance})
assert len(axes)==6,len(axes)
assert all(abs(a['distance_to_center']-26/3)<1e-6 for a in axes)
(p/'section_geometry.json').write_text(json.dumps({'section_x':-1,'edges':edges,'axes':axes,'inner_diameter':52,'target_circle_diameter':52/3},indent=2))
print(json.dumps({'actual_cylinder_axes':len(axes),'distance_to_center_mm':[a['distance_to_center'] for a in axes],'expected_radius_mm':26/3},indent=2))
