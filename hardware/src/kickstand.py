"""Slim folding kickstand (v2): low hinge plate glued to the back of the base + flat leg on an M4 pivot.
The open leg stops on a short wedge right beside the pivot (half the height of the old one).
Plate coords: x along the hinge axis, y up the case back (toward the top edge), z out from the case back."""
import numpy as np, trimesh, math
from manifold3d import Manifold, CrossSection
LEAN=15.0            # case leans back this much
ALPHA=50.0           # open leg angle from the case back (pointing down/back) -> leg is 35 deg from vertical
P_UP=75.0            # pivot height up the case back from the bottom edge (was 100: shorter leg)
PLATE_T=2.5          # plate thickness
H_P=5.5              # pivot axis height above the case surface
KD=10.0; PIN=4.4     # knuckle dia, M4 clearance
LW=22.0              # leg width
KW=6.0; GAP=0.5      # plate knuckle width, side gap
LT=5.0               # leg thickness (flat strap)
PW_=LW+2*(GAP+KW)    # plate width = hinge span (M4 x 40 bolt + nyloc)
PY0,PY1=-14.0,26.0   # plate extent along the case back
height=P_UP*math.cos(math.radians(LEAN)); beta=ALPHA-LEAN
LG=height/math.cos(math.radians(beta))      # pivot -> ground along the leg
OPEN=180-ALPHA                               # rotation from folded to open
def cyl_x(d,L,y,z,x0): return Manifold.cylinder(L,d/2,d/2,48).rotate([0,90,0]).translate([x0,y,z])
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
def rot_open(m,deg): return m.transform(np.asarray(trimesh.transformations.rotation_matrix(math.radians(deg),[1,0,0],[0,0,H_P])[:3,:]))
# ---- plate: thin base with two knuckle blocks, relief slot under the leg knuckle
xk=LW/2+GAP
plate=box(-PW_/2,PY0,0,PW_/2,PY1,PLATE_T)
for s in (-1,1):
    xa,xb=(xk,xk+KW) if s>0 else (-xk-KW,-xk)
    plate=plate+cyl_x(KD,KW,0,H_P,xa)+box(xa,-KD/2,0,xb,KD/2,H_P)
REL=math.sqrt((KD/2+0.4)**2-(H_P-PLATE_T)**2)        # half-length of the slot the leg knuckle swings through
plate=plate-box(-xk,-REL,-1,xk,REL,PLATE_T+1)
plate=plate-cyl_x(PIN,PW_+2,0,H_P,-PW_/2-1)
# short stop wedge right next to the pivot: the open leg's underside lands on it (was a 30 mm tall wedge)
a=math.radians(ALPHA); nin=np.array([-math.sin(a),-math.cos(a)])
p0=np.array([0,H_P])+nin*(LT/2)
def zline(y): t=(p0[0]-y)/math.cos(a); return p0[1]+math.sin(a)*t
W0,W1=-(KD/2+0.4),-11.0      # starts outside the leg knuckle's swing
pts=[(W0,PLATE_T-0.01),(W1,PLATE_T-0.01),(W1,zline(W1)),(W0,zline(W0))]
wedge=Manifold.extrude(CrossSection([[(float(y),float(z)) for y,z in pts[::-1]]]),LW-1.0).rotate([90,0,90]).translate([-(LW-1.0)/2,0,0])
plate=plate+wedge
# ---- leg (modelled folded: pointing +y along the case back), knuckle at the pivot
leg=cyl_x(KD,LW,0,H_P,-LW/2)+box(-LW/2,0,H_P-LT/2,LW/2,LG,H_P+LT/2)+cyl_x(LT,LW,LG,H_P,-LW/2)
leg=leg-cyl_x(PIN,LW+2,0,H_P,-LW/2-1)
def contact_angle(l=None):
    l=leg if l is None else l
    for d in np.arange(60,181,0.25):
        if (plate^rot_open(l,d)).volume()>0.05: return d
    return 181
def tm(m): o=m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
if __name__=='__main__':
    tp,tl=tm(plate),tm(leg)
    print('plate',tp.is_watertight,tp.bounds.round(1).tolist(),'%.1f cm3'%(tp.volume/1000))
    print('leg',tl.is_watertight,tl.bounds.round(1).tolist(),'%.1f cm3'%(tl.volume/1000))
    print('leg first touches the plate at %.2f deg (open target %.1f); leg %.0f deg from vertical; pivot to ground %.1f'%(contact_angle(),OPEN,beta,LG))
    print('folded: stands %.1f mm off the case back, reaches %.0f mm up from the bottom edge'%(H_P+KD/2,P_UP+LG+LT/2))
    print('foot lands %.0f mm behind the bottom-back edge'%(P_UP*math.sin(math.radians(LEAN))+LG*math.sin(math.radians(beta))))
