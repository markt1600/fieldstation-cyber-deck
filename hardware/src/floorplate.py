"""Floor plate: a 3 mm PETG plate glued to the case floor (Loctite 770 + 406, or VHB with 3M Primer 94).
It carries a low-walled pocket for the Pi 5 in its X1202-C1 case and heat-set insert bosses for the
70 x 50 mm soldered perfboard and the 65 x 55 mm GPIO breakout.
Panel coordinates (x right, y up, z = depth behind the panel front); the plate's underside sits on the floor."""
exec(open('frame.py').read())
from manifold3d import Manifold
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
FLOOR_Z=BASE_DEPTH-RIM_DROP
FP_T=3.0
FP=(52.0,85.0,250.0,211.0)              # x0,y0,x1,y1: clear of the post feet (x 21-47 / 255.5-281.5) and the floor fillet
FP_EXT=(18.0,100.5,56.0,190.0)          # extension to the left, between the left posts' feet (y 88.5-98.5 and 192-210)
FP_TAB=(246.0,128.0,258.5,172.0)        # small tab on the right for the strap loop (clear of the right posts' feet and the sensor cradle)
# Pi 5 + X1202-C1 case footprint and its pocket
PI=(145.0,105.0,145.0+98.75,105.0+90.2)
PK_CL,PK_WALL,PK_HT=0.5,2.0,6.0
# strap loops: a 20 mm hook-and-loop strap threads under a bar below and above the pocket and runs over the Pi case
STRAP_W,STRAP_GAP,STRAP_BAR,STRAP_LEN=26.0,3.0,2.5,8.0
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
    outline=rrect(FP[2]-FP[0],FP[3]-FP[1],6.0,(FP[0]+FP[2])/2,(FP[1]+FP[3])/2)+rrect(FP_EXT[2]-FP_EXT[0],FP_EXT[3]-FP_EXT[1],4.0,(FP_EXT[0]+FP_EXT[2])/2,(FP_EXT[1]+FP_EXT[3])/2)+rrect(FP_TAB[2]-FP_TAB[0],FP_TAB[3]-FP_TAB[1],3.0,(FP_TAB[0]+FP_TAB[2])/2,(FP_TAB[1]+FP_TAB[3])/2)
    p=Manifold.extrude(outline,FP_T).translate([0,0,z0])
    # Pi pocket walls
    a=PI[0]-PK_CL; b=PI[1]-PK_CL; c=PI[2]+PK_CL; d=PI[3]+PK_CL
    wall=box(a-PK_WALL,b-PK_WALL,z0-PK_HT,c+PK_WALL,d+PK_WALL,z0)-box(a,b,z0-PK_HT-1,c,d,z0+0.01)
    # finger notches in the long walls so the case lifts out
    for y in ((b+d)/2,):
        wall=wall-box(a-PK_WALL-1,y-12,z0-PK_HT-1,a+0.1,y+12,z0+0.01)-box(c-0.1,y-12,z0-PK_HT-1,c+PK_WALL+1,y+12,z0+0.01)
    p=p+wall
    # strap runs left to right over the front of the Pi case, through the finger notches in the side walls
    yc=(b+d)/2
    for xl in ((PB[2]+4.0+a-PK_WALL)/2, c+PK_WALL+1.0+STRAP_LEN/2):     # left: between perfboard bosses and wall; right: on a plate tab
        for sy in (-1,1):
            y0=yc+sy*STRAP_W/2; y1=y0+sy*3.0
            p=p+box(xl-STRAP_LEN/2,min(y0,y1),z0-STRAP_GAP-STRAP_BAR,xl+STRAP_LEN/2,max(y0,y1),z0)
        p=p+box(xl-STRAP_LEN/2,yc-STRAP_W/2-3.0,z0-STRAP_GAP-STRAP_BAR,xl+STRAP_LEN/2,yc+STRAP_W/2+3.0,z0-STRAP_GAP)
    for holes,h,d,l in ((pb_holes(),BOSS_H,M2_D,M2_L),(bo_holes(),BO_BOSS_H,INS_D,INS_L)):
        for x,y in holes:
            p=p+Manifold.cylinder(h,BOSS_D/2,BOSS_D/2,40).translate([x,y,z0-h])
            p=p-Manifold.cylinder(l+0.3,d/2,d/2,32).translate([x,y,z0-h-0.01])
    return p
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
    yc=(PI[1]+PI[3])/2
    ax.annotate('strap loops: the strap runs left to right\nover the front of the Pi case, through the\nfinger gaps in the pocket walls',xy=(252,yc),xytext=(146,83.5),fontsize=7,color='#c1121f',arrowprops=dict(arrowstyle='->',color='#c1121f'))
    ax.annotate('',xy=(138,yc),xytext=(150,90),arrowprops=dict(arrowstyle='->',color='#c1121f'))
    ax.set_xlim(10,262); ax.set_ylim(80,215); ax.set_aspect('equal'); ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm, up)')
    ax.set_title('Floor plate B5, seen from the front of the case (light = 3 mm plate, dark = pocket walls and M3 insert bosses)',fontsize=10)
    fig.tight_layout(); fig.savefig(fn,dpi=90)
if __name__=='__main__':
    draw('../docs/floor_plate.png'); m=build_floor_plate(); print('floor plate volume %.1f cm3'%(m.volume()/1000), 'perfboard holes',[(round(x,2),round(y,2)) for x,y in pb_holes()])
