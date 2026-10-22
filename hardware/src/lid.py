"""Lid: keyboard cradle + overlay. Lid panel coords: x 0..PW across, y 0 (user side) .. PH (hinge side).
z measured up from the lid floor."""
exec(open('frame.py').read().split('# ---------------- screen clamp insert positions')[0])
LID_DEPTH=30.0
KB_W,KB_D=286.0,149.0
KB_BACK,KB_FRONT=25.0,9.25            # body heights
KEY_H=2.08; BALL_H=5.55
FLOOR=1.0; OT=2.8                     # cradle floor, overlay thickness
CRADLE_H=FLOOR+KB_BACK                # cradle top = keyboard plate level (above cradle bottom)
PLATE_Z=VHB+CRADLE_H                  # plate level above lid floor
KX0=PW/2-KB_W/2; KX1=PW/2+KB_W/2; KY0=12.5; KY1=KY0+KB_D
C=0.5                                 # keyboard clearance in bay
CABLE_X=KX0+111.5+2.5                 # cable centre at the back edge
PASS_W,PASS_H=24.0,14.0; PASS_Y=PH-30.0  # USB-A pass-through slot in the overlay
# accessory tray (right half of the hinge strip) with a flush magnetic door
DOOR_X0,DOOR_X1=160.0,290.0; DOOR_Y0,DOOR_Y1=172.5,213.5; DOOR_R=4.0; DOOR_CL=0.3
MAG_S=4.56; MAG_P=4.56+0.2            # magnet cubes, pocket size
D_POCKET=2.1; D_PROUD=MAG_S-D_POCKET   # door pocket depth; cube stands proud under the door
BLOCK_POCKET=D_PROUD+MAG_S+0.1
MAGS=[(DOOR_X0+9,DOOR_Y0+8.5),(DOOR_X1-9,DOOR_Y0+8.5),(DOOR_X0+9,DOOR_Y1-8.5),(DOOR_X1-9,DOOR_Y1-8.5)]
# open pocket for the KVM remote: the hinge-strip cell left of the cable rib, exposed through the overlay
REM_X0,REM_X1,REM_Y0,REM_Y1,REM_R=9.75,77.75,172.0,214.0,4.0
OVL_STRETCH=(PW/2-3.0,1.3)          # left overlay half lengthened 1.3 mm next to the seam so its holes meet the cradle's (measured)
NOTCH=( 245.0, DOOR_Y0 )               # finger notch, centred between the two overlay screws below it
CX0,CX1,CY0,CY1=PW/2-147.5,PW/2+147.5,4.0,224.0
WALL=8.0; END=4.0; CH=4.0
def build_cradle():
    out=rrect(CX1-CX0,CY1-CY0,15,PW/2,(CY0+CY1)/2)
    fl=Manifold.extrude(out,FLOOR)
    walls=[rect(CX0,CY0,CX1,KY0-C),            # front wall
           rect(CX0,KY1+C,CX1,KY1+C+WALL),      # back wall
           rect(CX0,CY1-WALL,CX1,CY1),          # hinge wall
           rect(CX0,CY0,KX0-C,CY1),rect(KX1+C,CY0,CX1,CY1)]   # thin end walls
    walls.append(rect(PW/2-70-1.5,KY1+C,PW/2-70+1.5,CY1))   # rib in the cable half
    walls.append(rect(DOOR_X0-2,KY1+C,DOOR_X0+3,CY1))         # tray left wall (door rests on it)
    walls.append(rect(DOOR_X1-3,KY1+C,KX1+C,CY1))             # tray right wall
    for mx,my in MAGS: walls.append(rect(mx-6,my-6,mx+6,my+6))  # magnet blocks
    w=None
    for r in walls:
        m=Manifold.extrude(r^out,CRADLE_H); w=m if w is None else w+m
    c=fl+w
    # 45-degree ledges under the door's long edges (printable without support)
    for y0,dirn in ((KY1+C+WALL,1),(CY1-WALL,-1)):
        a=Manifold.cube([DOOR_X1-DOOR_X0,0.01,0.01]).translate([DOOR_X0,y0,CRADLE_H-0.01])
        top=Manifold.cube([DOOR_X1-DOOR_X0,4.0,2.0]).translate([DOOR_X0,y0 if dirn>0 else y0-4.0,CRADLE_H-2.0])
        low=Manifold.cube([DOOR_X1-DOOR_X0,0.01,0.01]).translate([DOOR_X0,y0,CRADLE_H-6.0])
        c=c+Manifold.batch_hull([top,low])
    for mx,my in MAGS: c=c-Manifold.cube([MAG_P,MAG_P,BLOCK_POCKET+0.01]).translate([mx-MAG_P/2,my-MAG_P/2,CRADLE_H-BLOCK_POCKET])
    # sloped support ribs: top follows keyboard underside (FLOOR at back -> FLOOR+(back-front) at front)
    zf=FLOOR+(KB_BACK-KB_FRONT)
    for i in range(6):
        x=KX0+12+i*(KB_W-24)/5
        a=Manifold.cube([3,1,zf]).translate([x-1.5,KY0,0]); b=Manifold.cube([3,1,FLOOR+0.01]).translate([x-1.5,KY1-1,0])
        c=c+Manifold.batch_hull([a,b])
    # front ledge so the thin front edge is fully supported
    c=c+Manifold.batch_hull([Manifold.cube([KB_W,1,zf]).translate([KX0,KY0,0]),Manifold.cube([KB_W,6,zf-0.6]).translate([KX0,KY0+5,0])])
    # outer bottom chamfer to clear the lid's floor fillet
    ch=Manifold.batch_hull([Manifold.extrude(out,0.01).translate([0,0,CH]),Manifold.extrude(out.offset(-CH,JoinType.Round),0.01)])
    c=c^(ch+Manifold.extrude(out,CRADLE_H).translate([0,0,CH]))
    # cable path: slot in back wall and notch in hinge wall, centre
    c=c-Manifold.cube([30,WALL+2,12]).translate([CABLE_X-15,KY1+C-1,CRADLE_H-12])   # cable drops in from above
    # heat-set inserts in wall tops
    for x in (CX0+22,PW/2-62,PW/2+62,CX1-22):
        for y in ((CY0+KY0-C)/2,KY1+C+WALL/2,CY1-WALL/2):
            if abs(x-PW/2)<32 and y>KY1: continue        # skip the cable slot
            c=c-Manifold.cylinder(6.0,2.0,2.0,32).translate([x,y,CRADLE_H-6+0.01])
    return c
def insert_points():
    pts=[]
    for x in (CX0+22,PW/2-62,PW/2+62,CX1-22):
        for y in ((CY0+KY0-C)/2,KY1+C+WALL/2,CY1-WALL/2):
            if abs(x-PW/2)<32 and y>KY1: continue
            pts.append((x,y))
    return pts
def build_overlay():
    p=rrect(PW,PH,PR,PW/2,PH/2)
    p=p-rrect(KB_W-9.0,KB_D-8.0,3,PW/2,(KY0+5.0+KY1-3.0)/2)       # laps 4.5 sides, 5 front, 3 back
    p=p-rrect(PASS_W,PASS_H,PASS_H/2-0.01,CABLE_X,PASS_Y)          # USB-A plug pass-through
    p=p-rrect(DOOR_X1-DOOR_X0,DOOR_Y1-DOOR_Y0,DOOR_R,(DOOR_X0+DOOR_X1)/2,(DOOR_Y0+DOOR_Y1)/2)   # tray door opening
    p=p-circ(18,NOTCH[0],NOTCH[1]-1.0)                              # finger notch
    p=p-rrect(REM_X1-REM_X0,REM_Y1-REM_Y0,REM_R,(REM_X0+REM_X1)/2,(REM_Y0+REM_Y1)/2)   # KVM remote pocket opening
    o=Manifold.extrude(p,OT)
    for x,y in insert_points():
        o=o-Manifold.cylinder(1.95,1.7,3.45,SEG).translate([x,y,OT-1.95+0.001])-Manifold.cylinder(OT+2,1.7,1.7,SEG).translate([x,y,-1])
    return o
def build_door():
    w,h=DOOR_X1-DOOR_X0-2*DOOR_CL,DOOR_Y1-DOOR_Y0-2*DOOR_CL
    d=Manifold.extrude(rrect(w,h,DOOR_R-DOOR_CL,(DOOR_X0+DOOR_X1)/2,(DOOR_Y0+DOOR_Y1)/2),OT)
    for mx,my in MAGS: d=d-Manifold.cube([MAG_P,MAG_P,D_POCKET+0.01]).translate([mx-MAG_P/2,my-MAG_P/2,-0.01])   # cube pockets in the underside
    return d
def tabs_region(tabs):
    L=rect(-10,-10,PW/2,PH+10)
    for yc,neck,head,depth in tabs:
        x0=PW/2
        L=L+poly([(x0-1,yc-neck/2),(x0,yc-neck/2),(x0+depth,yc-head/2),(x0+depth,yc+head/2),(x0,yc+neck/2),(x0-1,yc+neck/2)])
    return L
CRADLE_TABS=[(8.0,3.0,5.0,4.0),(KY1+C+WALL/2,3.0,5.0,4.0),(CY1-WALL/2,3.0,5.0,4.0)]
OVERLAY_TABS=[(8.75,5.0,8.0,6.0),(165.5,5.0,8.0,5.0),(221.0,5.0,8.0,5.0)]   # clear of the door opening and cable slot
def stretch_left(m,a=None,d=None):
    """lengthen a left half by d: everything left of x=a moves -d, and the band just left of a is repeated"""
    a,d=OVL_STRETCH if a is None else (a,d)
    big=1000
    lo=m^Manifold.cube([big,big,big]).translate([a-big,-big/2,-big/2])
    hi=m^Manifold.cube([big,big,big]).translate([a-d,-big/2,-big/2])
    return lo.translate([-d,0,0])+hi
def split(m,h,tabs):
    L=tabs_region(tabs)
    left=m^Manifold.extrude(L,h+2).translate([0,0,-1])
    right=m-Manifold.extrude(L.offset(0.25,JoinType.Miter),h+2).translate([0,0,-1])
    return left,right
if __name__=='__main__':
    cr=build_cradle(); ov=build_overlay()
    print('cradle',to_tm(cr).is_watertight,to_tm(cr).bounds.round(1).tolist())
    print('overlay',to_tm(ov).is_watertight,to_tm(ov).bounds.round(1).tolist())
    print('plate level %.2f, overlay top %.2f (lid seal 30), key tops %.2f, trackball top %.2f'%(PLATE_Z,PLATE_Z+OT,PLATE_Z+KEY_H,PLATE_Z+BALL_H))
