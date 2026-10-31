"""Floor plate: a 3 mm PETG plate glued to the case floor (Loctite 770 + 406, or VHB with 3M Primer 94).
It carries a low-walled pocket for the Pi 5 in its X1202-C1 case and heat-set insert bosses for the
70 x 50 mm soldered perfboard and the 65 x 55 mm GPIO breakout.
Panel coordinates (x right, y up, z = depth behind the panel front); the plate's underside sits on the floor."""
exec(open('frame.py').read())
from manifold3d import Manifold
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
FLOOR_Z=BASE_DEPTH-RIM_DROP
FP_T=3.0
FP=(18.0,88.0,284.5,211.0)              # whole flat floor: under all four post feet, kept clear of the speaker pods (y < 88) for their wires
SEAM_X=255.0                            # printed in two pieces (bed 256 mm): main plate + right strip, joined by dovetails
SEAM_TABS=(118.0,182.0)                 # dovetail centres along the seam
# speaker-pod brackets: an L-bracket epoxied to each pod's upper side wall, screwed down into the plate.
# They sit along the pods' upper edge (y 88-97), so the floor under the pods stays open for the speaker wires.
POD_BRK={'L':(64.0,90.0),'R':(PW-90.0,PW-64.0)}   # x range: inboard of each pod's rear cable hole (pod centre), so its wires can pass
BRK_Y0,BRK_Y1,BRK_LEG_T,BRK_FOOT_T,BRK_TOP=88.2,97.0,3.0,6.0,60.0
def brk_holes(k):
    x0,x1=POD_BRK[k]; return [(x0+6.0,(BRK_Y0+BRK_LEG_T+BRK_Y1)/2),(x1-6.0,(BRK_Y0+BRK_LEG_T+BRK_Y1)/2)]
def build_pod_bracket(k):
    x0,x1=POD_BRK[k]; zf=FLOOR_Z-FP_T                           # top of the plate
    foot=box(x0,BRK_Y0,zf-BRK_FOOT_T,x1,BRK_Y1,zf)
    leg=box(x0,BRK_Y0,BRK_TOP,x1,BRK_Y0+BRK_LEG_T,zf)
    b=foot+leg
    for xe in (x0,x1-3.0):                                       # end gussets
        b=b+Manifold.batch_hull([box(xe,BRK_Y0,zf-BRK_FOOT_T,xe+3.0,BRK_Y1,zf-BRK_FOOT_T+0.01),box(xe,BRK_Y0,zf-22.0,xe+3.0,BRK_Y0+BRK_LEG_T,zf-21.99)])
    for hx,hy in brk_holes(k):                                   # M3 insert from the underside of the foot
        b=b-Manifold.cylinder(6.0,2.0,2.0,32).translate([hx,hy,zf-6.0+0.01])
    return b
# Pi 5 + X1202-C1 case footprint and its pocket
PI=(145.0,105.0,145.0+98.75,105.0+90.2)
PK_CL,PK_WALL,PK_HT=0.5,2.0,6.0
# strap loops: a 20 mm hook-and-loop strap threads under a bar below and above the pocket and runs over the Pi case
STRAP_W,STRAP_GAP,STRAP_BAR,STRAP_LEN=26.0,3.0,2.5,8.0
STRAP_Y=PI[1]+(PI[3]-PI[1])/6     # bottom third of the Pi case, clear of the GPIO ribbon
# 70 x 50 perfboard, 2 mm holes on 65.5 x 45.5 centres (measured): M2 heat-set inserts (3.2 mm hole, 4.3 mm deep) on 6 mm bosses
# turned 90 deg (50 across, 70 up) and placed between the breakout and the Pi
PB=(82.0,100.0,132.0,170.0); PB_HX,PB_HY=45.5,65.5; BOSS_H,BOSS_D=6.0,8.0
INS_D,INS_L=4.0,5.7
M2_D,M2_L=3.2,4.0               # M2 insert hole (OD 3.2, up to 4 mm long); cut 4.3 mm deep
# 65 x 55 GPIO breakout turned 90 deg (55 across, 65 up) so the Pi ribbon runs straight; M3 holes ~48 x 57 (measured)
# far left, 70 mm from the Pi case so the ribbon clears the Pi's HDMI ports (needs >= 65 mm, measured)
BO=(20.0,102.0,75.0,167.0); BO_HX,BO_HY=48.0,57.0
BO_BOSS_H=8.2                    # two bosses on the side away from the Pi; the Pi side rests on the board's own GPIO connector (measured)
def bo_holes():
    cx,cy=(BO[0]+BO[2])/2,(BO[1]+BO[3])/2
    return [(cx-BO_HX/2,cy+sy*BO_HY/2) for sy in (-1,1)]   # only the two holes farthest from the Pi
def pb_holes():
    cx,cy=(PB[0]+PB[2])/2,(PB[1]+PB[3])/2
    return [(cx+sx*PB_HX/2,cy+sy*PB_HY/2) for sx in (-1,1) for sy in (-1,1)]
def build_floor_plate():
    z1=FLOOR_Z; z0=z1-FP_T
    outline=rrect(FP[2]-FP[0],FP[3]-FP[1],6.0,(FP[0]+FP[2])/2,(FP[1]+FP[3])/2)
    p=Manifold.extrude(outline,FP_T).translate([0,0,z0])
    # countersunk M3 holes for the screws that come up through the plate into the post feet and pod brackets
    def csk_up(hx,hy):
        return Manifold.cylinder(FP_T+0.02,1.7,1.7,24).translate([hx,hy,z0-0.01])+Manifold.cylinder(1.95,1.7,3.45,32).translate([hx,hy,z1-1.95+0.001])
    for n in POSTS:
        for hx,hy in foot_holes(n): p=p-csk_up(hx,hy)
    for k in POD_BRK:
        for hx,hy in brk_holes(k): p=p-csk_up(hx,hy)
    # Pi pocket walls
    a=PI[0]-PK_CL; b=PI[1]-PK_CL; c=PI[2]+PK_CL; d=PI[3]+PK_CL
    wall=box(a-PK_WALL,b-PK_WALL,z0-PK_HT,c+PK_WALL,d+PK_WALL,z0)-box(a,b,z0-PK_HT-1,c,d,z0+0.01)
    # finger notches in the long walls so the case lifts out
    for y in (STRAP_Y,):
        wall=wall-box(a-PK_WALL-1,y-12,z0-PK_HT-1,a+0.1,y+12,z0+0.01)-box(c-0.1,y-12,z0-PK_HT-1,c+PK_WALL+1,y+12,z0+0.01)
    p=p+wall
    # strap runs left to right over the front of the Pi case, through the finger notches in the side walls
    yc=STRAP_Y
    for xl in ((PB[2]+4.0+a-PK_WALL)/2, c+PK_WALL+0.5+STRAP_LEN/2):     # left: between perfboard bosses and wall; right: on a plate tab
        for sy in (-1,1):
            y0=yc+sy*STRAP_W/2; y1=y0+sy*3.0
            p=p+box(xl-STRAP_LEN/2,min(y0,y1),z0-STRAP_GAP-STRAP_BAR,xl+STRAP_LEN/2,max(y0,y1),z0)
        p=p+box(xl-STRAP_LEN/2,yc-STRAP_W/2-3.0,z0-STRAP_GAP-STRAP_BAR,xl+STRAP_LEN/2,yc+STRAP_W/2+3.0,z0-STRAP_GAP)
    for holes,h,d,l in ((pb_holes(),BOSS_H,M2_D,M2_L),(bo_holes(),BO_BOSS_H,INS_D,INS_L)):
        for x,y in holes:
            p=p+Manifold.cylinder(h,BOSS_D/2,BOSS_D/2,40).translate([x,y,z0-h])
            p=p-Manifold.cylinder(l+0.3,d/2,d/2,32).translate([x,y,z0-h-0.01])
    return p
def split_plate(m):
    """main plate (x < SEAM_X, with dovetail tabs) and right strip"""
    from manifold3d import CrossSection
    L=rect(-10,-10,SEAM_X,PH+10)
    for yc in SEAM_TABS:
        L=L+poly([(SEAM_X-1,yc-3.0),(SEAM_X,yc-3.0),(SEAM_X+6.0,yc-5.0),(SEAM_X+6.0,yc+5.0),(SEAM_X,yc+3.0),(SEAM_X-1,yc+3.0)])
    big=Manifold.extrude(L,200).translate([0,0,-100])
    bigc=Manifold.extrude(L.offset(0.25,JoinType.Miter),200).translate([0,0,-100])
    return m^big, m-bigc
def draw(fn):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
    from matplotlib.path import Path; from matplotlib.patches import PathPatch
    m=build_floor_plate(); fig,ax=plt.subplots(figsize=(9,6.5))
    for z,c in [(FLOOR_Z-1.5,'#ced4da'),(FLOOR_Z-4,'#6c757d')]:
        v=[];cd=[]
        for p in m.slice(z).to_polygons():
            p=np.asarray(p); v+=list(map(tuple,p))+[tuple(p[0])]; cd+=[Path.MOVETO]+[Path.LINETO]*(len(p)-1)+[Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(v,cd),fc=c,ec='k',lw=0.6))
    for lab,(x0,y0,x1,y1) in [('Pi 5 + X1202 case',PI),('perfboard, turned 90°\n50 × 70, holes 45.5 × 65.5\nM2 inserts',PB),('GPIO breakout\n55 × 65, holes 48 × 57\n2 bosses (8.2 mm) on the far side;\nthe Pi side rests on its connector\n70 mm from the Pi',BO)]:
        ax.add_patch(plt.Rectangle((x0,y0),x1-x0,y1-y0,fc='none',ec='r',ls='--')); ax.text((x0+x1)/2,(y0+y1)/2,lab,ha='center',va='center',fontsize=8,color='r')
    yc=STRAP_Y
    ax.annotate('strap loops: the strap runs left to right\nover the front of the Pi case, through the\nfinger gaps in the pocket walls',xy=(252,yc),xytext=(160,165),fontsize=7,color='#c1121f',arrowprops=dict(arrowstyle='->',color='#c1121f'))
    ax.annotate('',xy=(138,yc),xytext=(165,163),arrowprops=dict(arrowstyle='->',color='#c1121f'))
    ax.plot([SEAM_X,SEAM_X],[FP[1],FP[3]],'k--',lw=0.8); ax.text(SEAM_X+1,FP[3]+2,'seam (dovetailed)',fontsize=7)
    for n,(x,y) in POSTS.items(): ax.text(x+(14 if x<PW/2 else -14),y+(8 if n in ('TL','TR') else 8),'post '+n,ha='center',fontsize=7,color='#1d3557')
    for k,(bx0,bx1) in POD_BRK.items(): ax.text((bx0+bx1)/2,FP[1]-5,'pod bracket',ha='center',fontsize=7,color='#1d3557')
    ax.set_xlim(10,290); ax.set_ylim(75,218);
    ax.set_aspect('equal'); ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm, up)')
    ax.set_title('Floor plate B5, seen from the front of the case (light = 3 mm plate, dark = walls and bosses)\nposts and pod brackets: M3 × 8 countersunk screws up through the plate into inserts in their feet',fontsize=10)
    fig.tight_layout(); fig.savefig(fn,dpi=90)
if __name__=='__main__':
    draw('../docs/floor_plate.png'); m=build_floor_plate(); print('floor plate volume %.1f cm3'%(m.volume()/1000), 'perfboard holes',[(round(x,2),round(y,2)) for x,y in pb_holes()])
