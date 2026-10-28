"""Single circular transitions, extruded across the arm width."""
import math
import FreeCAD as A
import Part
V=A.Vector

def profile(y1,z1,y2,z2,top):
    # Local coordinates: x is assembly Y, y is assembly Z.
    span=y2-y1
    rise=abs(z2-z1)
    assert span>rise>0
    r=(span*span+rise*rise)/(2*rise)
    # The circle is tangent to the flat thin section, at the higher end.
    center=V(y2 if z2>z1 else y1,max(z1,z2)-r,0)
    p0=V(y1,z1,0); finish=V(y2,z2,0)
    v1=p0-center; v2=finish-center
    mid=center+(v1+v2).normalize()*r
    edges=[]
    def line(a,b):
        if (a-b).Length>1e-8:edges.append(Part.LineSegment(a,b))
    edges.append(Part.Arc(p0,mid,finish))
    line(finish,V(y2,top,0));line(V(y2,top,0),V(y1,top,0));line(V(y1,top,0),p0)
    return edges

def placement(halfwidth):
    return A.Placement(V(-halfwidth,0,0),A.Rotation(V(0,1,0),V(0,0,1),V(1,0,0),'ZXY'))

def solid(y1,z1,y2,z2,halfwidth,top):
    wire=Part.Wire([g.toShape() for g in profile(y1,z1,y2,z2,top)])
    shape=Part.Face(wire).extrude(V(0,0,2*halfwidth))
    shape.Placement=placement(halfwidth)
    return shape
