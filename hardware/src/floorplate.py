"""Floor plate: a 3 mm PETG plate glued to the case floor (Loctite 770 + 406, or VHB with 3M Primer 94).
It carries a low-walled pocket for the Pi 5 in its X1202-C1 case and heat-set insert bosses for the
70 x 50 mm soldered perfboard. GPIO breakout bosses to come once its hole pattern is known.
Panel coordinates (x right, y up, z = depth behind the panel front); the plate's underside sits on the floor."""
exec(open('frame.py').read())
from manifold3d import Manifold
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
FLOOR_Z=BASE_DEPTH-RIM_DROP
FP_T=3.0
FP=(52.0,85.0,250.0,200.0)              # x0,y0,x1,y1: clear of the post feet (x 21-47 / 255.5-281.5) and the floor fillet
# Pi 5 + X1202-C1 case footprint and its pocket
PI=(145.0,105.0,145.0+98.75,105.0+90.2)
PK_CL,PK_WALL,PK_HT=0.5,2.0,6.0
# 70 x 50 perfboard, M3 holes on 65.5 x 45.5 centres (measured), on 6 mm insert bosses
PB=(60.0,90.0,130.0,140.0); PB_HX,PB_HY=65.5,45.5; BOSS_H,BOSS_D=6.0,8.0
INS_D,INS_L=4.0,5.7
def pb_holes():
    cx,cy=(PB[0]+PB[2])/2,(PB[1]+PB[3])/2
    return [(cx+sx*PB_HX/2,cy+sy*PB_HY/2) for sx in (-1,1) for sy in (-1,1)]
def build_floor_plate():
    z1=FLOOR_Z; z0=z1-FP_T
    p=Manifold.extrude(rrect(FP[2]-FP[0],FP[3]-FP[1],6.0,(FP[0]+FP[2])/2,(FP[1]+FP[3])/2),FP_T).translate([0,0,z0])
    # Pi pocket walls
    a=PI[0]-PK_CL; b=PI[1]-PK_CL; c=PI[2]+PK_CL; d=PI[3]+PK_CL
    wall=box(a-PK_WALL,b-PK_WALL,z0-PK_HT,c+PK_WALL,d+PK_WALL,z0)-box(a,b,z0-PK_HT-1,c,d,z0+0.01)
    # finger notches in the long walls so the case lifts out
    for y in ((b+d)/2,):
        wall=wall-box(a-PK_WALL-1,y-12,z0-PK_HT-1,a+0.1,y+12,z0+0.01)-box(c-0.1,y-12,z0-PK_HT-1,c+PK_WALL+1,y+12,z0+0.01)
    p=p+wall
    for x,y in pb_holes():
        p=p+Manifold.cylinder(BOSS_H,BOSS_D/2,BOSS_D/2,40).translate([x,y,z0-BOSS_H])
        p=p-Manifold.cylinder(INS_L+0.5,INS_D/2,INS_D/2,32).translate([x,y,z0-BOSS_H-0.01])
    return p
if __name__=='__main__':
    m=build_floor_plate(); print('floor plate volume %.1f cm3'%(m.volume()/1000), 'perfboard holes',[(round(x,2),round(y,2)) for x,y in pb_holes()])
