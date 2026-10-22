"""FIELDSTATION frame for Peli 1400. Panel coords: x right, y up (front view), mm.
Panel front face z=0, back z=T (parts behind the panel live at z>T)."""
import numpy as np, trimesh, math
from manifold3d import Manifold, CrossSection, JoinType
SEG=48
# ---------------- global layout ----------------
PW,PH,PR,T=302.5,228.8,19.0,4.0
RIM_DROP=8.0; BASE_DEPTH=99.0; VHB=1.1
SC_W,SC_H,SC_T=190.5,115.2,16.8           # cased screen
SC_X0=(PW-SC_W)/2; SC_Y0=98.8              # case lower-left
SC_CX,SC_CY=PW/2,SC_Y0+SC_H/2
WIN_W,WIN_H=156.0,88.0                    # visible window (centred on case)
POD=80.0; POD_DEPTH=78.0; PODS=[(52.0,48.0),(PW-52.0,48.0)]; POD_SCREW=36.0; GRILLE_R=33.0
PK_W,PK_H=106.0,76.0; PK_CX,PK_CY=PW/2,48.0; PK_DEPTH=18.0   # pocket, depth from panel front
# AIR on the right: the screen's HDMI and micro-USB plugs come out of its left edge
AIR_C=(PW-25.5,SC_CY); TEMP_C=(25.5,SC_CY)
CLAMP_WALL,CLAMP_ARM=9.0,24.0
POSTS={'TL':(26.0,205.0),'TR':(PW-26.0,205.0),'ML':(26.0,93.5),'MR':(PW-26.0,93.5)}
TRAY_INS=[(PW/2-48,5.0),(PW/2+48,5.0),(PW/2-48,SC_Y0-6.4),(PW/2+48,SC_Y0-6.4)]
# ---------------- helpers ----------------
def rrect(w,h,r,cx=0,cy=0):
    return CrossSection.square([w-2*r,h-2*r],center=True).offset(r,JoinType.Round,circular_segments=SEG).translate([cx,cy])
def circ(d,cx=0,cy=0,seg=SEG): return CrossSection.circle(d/2,seg).translate([cx,cy])
def rect(x0,y0,x1,y1): return CrossSection.square([x1-x0,y1-y0]).translate([x0,y0])
def poly(pts): return CrossSection([pts])
def csk(x,y,depth=T+2):
    """countersunk M3 from the front face (z=0)"""
    cone=Manifold.cylinder(1.95,3.45,1.7,SEG).translate([x,y,-0.001])   # fits ISO 10642 M3 heads flush
    return cone+Manifold.cylinder(depth,1.7,1.7,SEG).translate([x,y,-1])
def to_tm(m):
    o=m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
# ---------------- screen clamp insert positions ----------------
def clamp_holes():
    pts=[]
    corners=[(SC_X0,SC_Y0,1,1),(SC_X0+SC_W,SC_Y0,-1,1),(SC_X0,SC_Y0+SC_H,1,-1),(SC_X0+SC_W,SC_Y0+SC_H,-1,-1)]
    for cx,cy,sx,sy in corners:
        for lx,ly in [(-CLAMP_WALL/2,CLAMP_ARM-8),(CLAMP_ARM-8,-CLAMP_WALL/2)]:
            pts.append((cx+sx*lx,cy+sy*ly))
    return pts
# ---------------- 2D panel ----------------
def panel_2d():
    p=rrect(PW,PH,PR,PW/2,PH/2)
    p=p-rrect(WIN_W,WIN_H,2,SC_CX,SC_CY)
    p=p-rrect(PK_W,PK_H,3,PK_CX,PK_CY)
    # pod grilles: 3.0 mm holes, hex pitch 4.6 inside r33
    for cx,cy in PODS:
        pitch=4.6; rows=int(GRILLE_R*2/(pitch*0.866))+2
        for j in range(-rows,rows+1):
            yy=j*pitch*0.866; off=(pitch/2 if j%2 else 0)
            for i in range(-12,13):
                xx=i*pitch+off
                if math.hypot(xx,yy)<=GRILLE_R-1.5: p=p-circ(3.0,cx+xx,cy+yy,16)
    # AIR louvres over PMS7003 face (12 x 48), solid bar in the middle as inlet/outlet divider
    ax,ay=AIR_C
    for k in range(-5,6):          # inlet chamber now runs to the sensor's end, so all 10 louvres open into it
        if k==0: continue
        y=ay+k*4.2; p=p-rrect(10,2.0,0.99,ax,y)
    # TEMP column vent slots
    tx,ty=TEMP_C
    for k in range(-7,8):
        p=p-rrect(22,2.0,0.99,tx,ty+k*5.0)
    return p
def holes_3d():
    h=[]
    for cx,cy in PODS:
        for dx in (-POD_SCREW,POD_SCREW):
            for dy in (-POD_SCREW,POD_SCREW): h.append(csk(cx+dx,cy+dy))
    for x,y in clamp_holes(): h.append(csk(x,y))
    for x,y in POSTS.values(): h.append(csk(x,y))
    for x,y in TRAY_INS: h.append(csk(x,y))
    for dx,dy in [(-13.0,-12.0),(13.0,-12.0),(0.0,-32.2)]: h.append(csk(AIR_C[0]+dx,AIR_C[1]+dy))   # PMS7003 cradle v2
    return h
def chamfer_window():
    """45-degree chamfer on the front edge of the screen window and pocket"""
    c=Manifold.extrude(rrect(WIN_W+3,WIN_H+3,3.5,SC_CX,SC_CY),0.01).translate([0,0,-0.005])
    c=Manifold.batch_hull([c,Manifold.extrude(rrect(WIN_W,WIN_H,2,SC_CX,SC_CY),0.01).translate([0,0,1.5])])
    return c
def dovetail_left_region():
    """region belonging to the LEFT half: x<148 plus tabs into the right"""
    L=rect(-10,-10,PW/2,PH+10)
    for yc,neck,head,depth in [(98.2,8.0,13.0,8.0),(209.7,8.0,13.0,8.0)]:   # bottom joint bridged by the tray flange
        x0=PW/2
        L=L+poly([(x0-1,yc-neck/2),(x0,yc-neck/2),(x0+depth,yc-head/2),(x0+depth,yc+head/2),(x0,yc+neck/2),(x0-1,yc+neck/2)])
    return L
def build_panel():
    p2=panel_2d()
    full=Manifold.extrude(p2,T)
    full=full-chamfer_window()
    for h in holes_3d(): full=full-h
    L=dovetail_left_region()
    left=full^Manifold.extrude(L,T+2).translate([0,0,-1])
    right=full-Manifold.extrude(L.offset(0.25,JoinType.Miter),T+2).translate([0,0,-1])
    return full,left,right
# ---------------- port tray ----------------
USB=[(PK_CX-30,PK_CY+18.5),(PK_CX,PK_CY+18.5),(PK_CX+30,PK_CY+18.5)]
CTRL_Y=PK_CY-14                    # controls row (raised to make room for the keyboard slot below it)
BTN=(PK_CX-40,CTRL_Y); DCJ=(PK_CX-18,CTRL_Y); TOG=(PK_CX+4,CTRL_Y); POT=(PK_CX+32,CTRL_Y)
BTN_HOLE=12.1                      # power button: 11.7 mm thread (measured)
DCJ_HOLE=11.1                      # 12 V DC jack: 10.7 mm thread (measured)
POT_HOLE=6.4                       # volume pot: 6 mm bushing (measured)
POT_TAB_R,POT_TAB_D=7.55,2.8       # pot anti-rotation tab: 7.55 mm from shaft centre, 2.35 mm long (measured); round hole fits it any way round
TOG_HOLE=16.3                      # audio on/off toggle: 15.9 mm body passes through (measured); wider front section holds it
KB_PASS_W,KB_PASS_H=24.0,12.0
KB_PASS=(122.2,PK_CY-PK_H/2+1.5+KB_PASS_H/2)   # keyboard USB-A pass-through at the very bottom, same x as the lid slot
def build_tray():
    WALLT=3.0; FLOOR=3.0
    zf=PK_DEPTH-T                         # floor front face behind panel back
    inner=rrect(PK_W,PK_H,3,PK_CX,PK_CY)
    outer=rrect(PK_W+2*WALLT,PK_H+2*WALLT,4,PK_CX,PK_CY)
    flange=rect(PK_CX-57.5,0.5,PK_CX+57.5,SC_Y0-3.0)
    fl=Manifold.extrude(flange,6.0)
    taper=Manifold.extrude(outer,0.01).translate([0,0,zf])
    body=Manifold.batch_hull([fl,taper])+Manifold.extrude(outer,zf+FLOOR)
    body=body-Manifold.extrude(inner,zf).translate([0,0,-0.01])
    def through(cs): return Manifold.extrude(cs,zf+FLOOR+2).translate([0,0,-1])
    for x,y in USB:
        body=body-through(circ(24.2,x,y))
        for dx,dy in [(-9.5,12),(9.5,-12)]: body=body-through(circ(3.3,x+dx,y+dy,24))
    body=body-through(circ(BTN_HOLE,*BTN))-through(circ(DCJ_HOLE,*DCJ))-through(circ(TOG_HOLE,*TOG))-through(circ(POT_HOLE,*POT))-through(circ(POT_TAB_D,POT[0],POT[1]+POT_TAB_R))
    body=body-through(rrect(KB_PASS_W,KB_PASS_H,KB_PASS_H/2-0.01,*KB_PASS))
    for x,y in TRAY_INS: body=body-Manifold.cylinder(6.0,2.0,2.0,32).translate([x,y,-0.01])
    return body.translate([0,0,T])        # place behind panel
# ---------------- posts ----------------
POST_H=BASE_DEPTH-RIM_DROP-T-VHB         # floor to panel back, less VHB tape
def build_post(name):
    """10 mm column; foot reaches inward onto the flat floor (the case floor has a ~18 mm fillet at the walls)"""
    x,y=POSTS[name]; c=10.0
    sx=1 if x<PW/2 else -1
    fx0,fx1=(x-5,x+21) if sx>0 else (x-21,x+5)
    fy0,fy1=(y-13,y+5) if name in ('TL','TR') else (y-5,y+5)
    foot=rect(fx0,fy0,fx1,fy1)
    col=Manifold.extrude(rrect(c,c,2,x,y),POST_H)
    ft=Manifold.extrude(foot,3.0)
    gus=Manifold.batch_hull([Manifold.extrude(foot,0.01),Manifold.extrude(rrect(c,c,2,x,y),0.01).translate([0,0,16])])
    post=col+ft+gus
    return post-Manifold.cylinder(6.5,2.0,2.0,32).translate([x,y,POST_H-6.5+0.01])
