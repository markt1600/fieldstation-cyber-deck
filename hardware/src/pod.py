import numpy as np, trimesh
from manifold3d import Manifold, CrossSection
# ---------- parameters (mm) ----------
W=80.0; H=80.0; D=78.0         # overall pod (shortened for the 94 mm-deep base)
R=4.0                           # vertical edge radius
WALL=2.5; BACK=3.0
BAFFLE=5.0; RIM=6.0             # baffle plate + gasket rim toward panel
BODY_D=D-BAFFLE-RIM             # 74
CUT=52.5                        # driver through-cutout (spec 52)
SEAT=65.6; SEAT_DEPTH=1.5       # square locating recess, r4 corners (clears square frame or round frame with tabs)
RIM_ID=66.4                     # square rim opening, r4 corners
INS=36.0                        # corner screw/insert position (+/-)
INS_HOLE=4.0; INS_DEPTH=7.0     # M3 heat-set (4.0 mm hole)
CLR=3.4                         # M3 clearance
CABLE=9.0                       # rear cable hole (doubled)
DRV_PITCH=46.5                  # measured adjacent hole c-c (square pattern)
DRV_PCD=DRV_PITCH*2**0.5        # 58.72 bolt circle
DRV_PILOT=3.3                   # pilot for M4 / #8 screw (driver holes are 5 mm)
SEG=96
def rrect(w,h,r):
    return CrossSection.square([w-2*r,h-2*r],center=True).offset(r,join_type=CrossSection.JoinType.Round if hasattr(CrossSection,'JoinType') else 1,circular_segments=48)
def circ(d): return CrossSection.circle(d/2,SEG)
def cyl(d,h,z0=0,x=0,y=0): return Manifold.cylinder(h,d/2,d/2,SEG).translate([x,y,z0])
# ---------- body (printed back-down) ----------
outer=rrect(W,H,R).extrude(BODY_D)
inner=rrect(W-2*WALL,H-2*WALL,max(R-WALL,0.5)).extrude(BODY_D).translate([0,0,BACK])
body=outer-inner
# corner insert blocks: top 12 mm solid square in each corner, 45-degree taper underneath
iw=(W-2*WALL)/2   # 37.5
blk=12.0
for sx in (-1,1):
  for sy in (-1,1):
    a=INS-4.5     # inner edge of block
    sq=CrossSection.square([iw-a+0.5, iw-a+0.5]).translate([a, a])
    top=sq.extrude(blk).translate([0,0,BODY_D-blk])
    # taper: hull of block bottom face and a tiny square in the corner lower down
    tip=CrossSection.square([0.5,0.5]).translate([iw-0.2,iw-0.2]).extrude(0.1).translate([0,0,BODY_D-blk-(iw-a)])
    piece=Manifold.batch_hull([top,tip]) if hasattr(Manifold,'batch_hull') else (top+tip).hull()
    m=piece.scale([sx,sy,1])
    body=body+m
    body=body-cyl(INS_HOLE,INS_DEPTH+0.01,BODY_D-INS_DEPTH,sx*INS,sy*INS)
# magnet bosses on the inner walls (pinwheel layout, clear of corner inserts, driver screws and terminal notches)
MAG_S=4.56; MAG_P=4.56+0.2          # magnet cubes, pocket size
B_POCKET=2.6; PROUD=MAG_S-B_POCKET   # baffle pocket depth; cube stands proud of the baffle by this
BODY_POCKET=PROUD+MAG_S+0.1          # body pocket takes the proud part plus its own cube
MAGS=[(26.0,33.0),(-26.0,-33.0),(33.0,-26.0),(-33.0,26.0)]
iw2=(W-2*WALL)/2
for mx,my in MAGS:
    # boss: 9 x 9 at the top, tapering back into the wall at 45 degrees below (prints without support)
    if abs(my)>abs(mx):
        sy=1 if my>0 else -1
        top=Manifold.cube([9,iw2-(abs(my)-4.5),9]).translate([mx-4.5,0,BODY_D-9]); top=top.translate([0,(abs(my)-4.5) if sy>0 else -iw2,0])
        root=Manifold.cube([9,0.5,0.01]).translate([mx-4.5,(iw2-0.5) if sy>0 else -iw2,BODY_D-9-(iw2-(abs(my)-4.5))])
    else:
        sx=1 if mx>0 else -1
        top=Manifold.cube([iw2-(abs(mx)-4.5),9,9]).translate([0,my-4.5,BODY_D-9]); top=top.translate([(abs(mx)-4.5) if sx>0 else -iw2,0,0])
        root=Manifold.cube([0.5,9,0.01]).translate([(iw2-0.5) if sx>0 else -iw2,my-4.5,BODY_D-9-(iw2-(abs(mx)-4.5))])
    body=body+Manifold.batch_hull([top,root])
    body=body-Manifold.cube([MAG_P,MAG_P,BODY_POCKET+0.01]).translate([mx-MAG_P/2,my-MAG_P/2,BODY_D-BODY_POCKET])
# rear cable hole (near bottom of back panel), through back
body=body-Manifold.cylinder(BACK+2,CABLE/2,CABLE/2,48).translate([0,-(H/2-WALL-8),-1])
# ---------- baffle + rim (printed glue-face down) ----------
plate=rrect(W,H,R).extrude(BAFFLE)
rim=(rrect(W,H,R)-rrect(RIM_ID,RIM_ID,4)).extrude(RIM).translate([0,0,BAFFLE])
baf=plate+rim
baf=baf-cyl(CUT,BAFFLE+2,-1)
# single terminal notch on the -y side (toward the cable hole). 38 mm wide (block is 31.2) and cut from the centre
# outward, so its walls meet the round hole at an obtuse angle: no thin slivers left to snap off.
TN_HALF,TN_R=19.0,31.5
baf=baf-Manifold.cube([2*TN_HALF,TN_R,BAFFLE+2]).translate([-TN_HALF,-TN_R,-1])
baf=baf-rrect(SEAT,SEAT,4).extrude(SEAT_DEPTH+0.01).translate([0,0,BAFFLE-SEAT_DEPTH])
for sx in (-1,1):
  for sy in (-1,1):
    baf=baf-cyl(DRV_PILOT,BAFFLE+2,-1,sx*DRV_PITCH/2,sy*DRV_PITCH/2)
for sx in (-1,1):
  for sy in (-1,1):
    baf=baf-cyl(CLR,BAFFLE+RIM+2,-1,sx*INS,sy*INS)
for mx,my in MAGS: baf=baf-Manifold.cube([MAG_P,MAG_P,B_POCKET+0.01]).translate([mx-MAG_P/2,my-MAG_P/2,-0.01])   # cube pockets in the baffle's underside
def save(m,fn):
    mesh=m.to_mesh(); t=trimesh.Trimesh(mesh.vert_properties[:,:3],mesh.tri_verts,process=False)
    t.export(fn); return t
tb=save(body,'pod_body.stl'); tf=save(baf,'pod_baffle.stl')
# assembly (baffle on top of body) for preview
asm=body+baf.translate([0,0,BODY_D])
ta=save(asm,'_pod_assembly.stl')
# ---------- volume check ----------
air=(inner ^ outer) - body
net=air.volume()/1e6-0.025   # minus ~25 cc driver displacement
print('body watertight',tb.is_watertight,'baffle',tf.is_watertight)
print('internal air L %.3f, net after driver L %.3f'%(air.volume()/1e6,net))
fs,qts,vas=89.5,0.61,0.53
for vb,lab in [(net,'empty'),(net*1.2,'with polyfill')]:
    a=vas/vb; print(lab,'fc %.0f Hz Qtc %.2f'%(fs*np.sqrt(1+a),qts*np.sqrt(1+a)))
