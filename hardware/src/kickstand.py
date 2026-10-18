"""Folding kickstand: hinge plate glued to the back of the base + leg on an M4 pivot.
Plate coords: x along the hinge axis, y up the case back (toward the top edge), z out from the case back."""
import numpy as np, trimesh, math
from manifold3d import Manifold, CrossSection
LEAN=15.0            # case leans back this much
ALPHA=50.0           # open leg angle from the case back (pointing down/back) -> leg is 35 deg from vertical
P_UP=100.0           # pivot height up the case back from the bottom edge
H_P=7.0              # pivot axis height above the case surface
PLATE_T=3.0; PW_,PY0,PY1=50.0,-26.0,36.0
KD=12.0; PIN=4.4     # knuckle dia, M4 clearance
KW=8.0; GAP=0.6; LW=50.0-2*(KW+4.0)-2*GAP   # leg knuckle width between plate knuckles
LT=8.0               # leg thickness
height=P_UP*math.cos(math.radians(LEAN)); beta=ALPHA-LEAN
LG=height/math.cos(math.radians(beta))      # pivot -> ground along the leg
def cyl_x(d,L,y,z,x0): return Manifold.cylinder(L,d/2,d/2,48).rotate([0,90,0]).translate([x0,y,z])
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
# ---- plate
plate=box(-PW_/2,PY0,0,PW_/2,PY1,PLATE_T)
xk=LW/2+GAP          # inner face of the plate knuckles
for s in (-1,1):
    xa,xb=(xk,xk+KW) if s>0 else (-xk-KW,-xk)
    plate=plate+cyl_x(KD,KW,0,H_P,xa)+box(xa,-KD/2,0,xb,KD/2,H_P)
# open-angle stop wedge under the leg (between the knuckles is where the leg swings, so wedges sit under the leg's path)
a=math.radians(ALPHA); u=np.array([-math.cos(a),math.sin(a)]); nin=np.array([-math.sin(a),-math.cos(a)])
p0=np.array([0,H_P])+nin*(LT/2)
def zline(y): s=(p0[0]-y)/math.cos(a); return p0[1]+math.sin(a)*s
ys=[-7.0,PY0+1.0]
pts=[(ys[0],PLATE_T),(ys[1],PLATE_T),(ys[1],zline(ys[1])),(ys[0],zline(ys[0]))]
wedge=Manifold.extrude(CrossSection([[ (float(y),float(z)) for y,z in pts[::-1]]]),LW-1.0).rotate([90,0,90]).translate([-(LW-1.0)/2,0,0])
plate=plate+wedge
plate=plate-cyl_x(PIN,PW_+2,0,H_P,-PW_/2-1)
plate=plate-box(-(LW/2+GAP),-7.0,-1,LW/2+GAP,7.0,PLATE_T+1)   # relief under the leg knuckle
# ---- leg (modelled folded: pointing +y along the case back), knuckle at the pivot
leg=cyl_x(KD,LW,0,H_P,-LW/2)+box(-LW/2,0,H_P-LT/2,LW/2,LG,H_P+LT/2)
leg=leg+cyl_x(LT,LW,LG,H_P,-LW/2)            # rounded foot end
leg=leg-cyl_x(PIN,LW+2,0,H_P,-LW/2-1)
def tm(m): o=m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
tp,tl=tm(plate),tm(leg)
# open-position check: rotate leg 180-ALPHA about the pivot axis and test against the plate (excluding knuckle overlap)
R=trimesh.transformations.rotation_matrix(math.radians(180-ALPHA),[1,0,0],[0,0,H_P])
lo=leg.transform(R[:3,:]) if hasattr(leg,'transform') else None
open_leg=Manifold.cube([1,1,1])  # placeholder
ov=(plate ^ leg.transform(np.asarray(R[:3,:]))).volume() if hasattr(leg,'transform') else -1
print('plate watertight',tp.is_watertight,'bounds',tp.bounds.round(1).tolist())
print('leg watertight',tl.is_watertight,'leg pivot-to-ground %.1f mm, leg %.0f deg from vertical when open'%(LG,beta))
print('overlap plate vs open leg (should be ~0, wedge touching): %.2f mm3'%ov)
print('folded leg reaches %.0f mm up the case back from the bottom edge'%(P_UP+LG+LT/2))
foot_back=P_UP*math.sin(math.radians(LEAN))+LG*math.sin(math.radians(beta))
print('foot lands %.0f mm behind the bottom-back edge'%foot_back)
tp.export('kickstand_plate.stl'); tl.export('kickstand_leg.stl')
