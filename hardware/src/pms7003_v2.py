"""PMS7003 cradle with a ducted snout. Local coords: x across the 12 mm face, y along the 48 mm face (y+ = inlet end,
where the adapter board and Dupont plugs are), z = 0 at the panel back, + into the case."""
import trimesh
from manifold3d import Manifold
SL,ST,SD=48.0,12.0,37.0; CL=0.4
iw,ih=ST+CL,SL+CL                 # x, y interior
SNOUT=34.0                        # sensor face sits this far behind the panel (room for the Dupont plugs + wire bend)
WALL=2.0; LIP=1.2; FL_T=7.0
# Adapter board (measured): lies flat on the +x (label) face, 3.5 mm above it, 1.6 thick; reaches 12.77 mm back
# from the inlet face, overhangs the inlet face by 6.5 mm and the board end by 9 mm. Dupont plugs hang off its
# inlet-side edge toward the panel, over y ~12..23.
BRD_GAP,BRD_T=3.5,1.6; BRD_BACK,BRD_OVER,BRD_END=12.77,6.5,9.0; BRD_Y0=12.0; PLUG_L=16.0
WALL_B=1.2                       # thin duct wall on the board side, tucked under the board
INS=4.0; INS_D=6.0
INSERTS=[(-13.0,-12.0),(13.0,-12.0),(0.0,-(ih/2+WALL+6.0))]
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
ox,oy=iw/2+WALL,ih/2+WALL; oxb=iw/2+WALL_B   # -x side, +x (board) side
# Measured on the sensor face, from the board end: inlet slot 4.73..14.85 mm, outlet starts 30.45 mm.
# Sensor spans y -24..+24 with the board end at +24, so: inlet y +9.15..+19.27, outlet y < -6.45.
INLET_NEAR=24.0-4.73
END0=INLET_NEAR+1.0            # inner face of the duct's end wall (1 mm clear of the inlet slot)
END1=END0+3.0                  # wall is 3 mm thick and lands on the sensor face, short of its end,
                               # so the area beyond the sensor's end stays open for the board and Dupont plugs
# snout duct, open both ends, with a divider rib between inlet and outlet
snout=box(-ox,-oy,0,oxb,END1,SNOUT)-box(-iw/2,-ih/2,-1,iw/2,END0,SNOUT+1)
snout=snout+box(-iw/2,-1.0,0,iw/2,1.0,SNOUT)
# face stop: lip at the back of the snout; the sensor face (with a foam gasket) presses on it all round
stop=box(-ox,-oy,SNOUT-1.5,oxb,END1,SNOUT)-box(-iw/2+LIP,-ih/2+LIP,SNOUT-2,iw/2-LIP,END0,SNOUT+1)
# sleeve behind: long sides + closed outlet end; inlet end open so the adapter board can plug on
z0,z1=SNOUT,SNOUT+SD+CL
sleeve=box(-ox,-oy,z0,oxb,23.0,z1)-box(-iw/2,-ih/2,z0-1,iw/2,ih/2+1,z1+1)   # side walls stop 1 mm short of the board end
# window in the board-side wall so the board's connector slides past it (open to the plug end)
_wt=z0+BRD_BACK+1.5                       # window top; it rises at 45 deg toward the open end so it prints without support
sleeve=sleeve-Manifold.hull(box(iw/2-0.5,BRD_Y0-2.0,z0-1,oxb+1,BRD_Y0,_wt)+
                            box(iw/2-0.5,ih/2,z0-1,oxb+1,ih/2+5,_wt+(ih/2-BRD_Y0)))
# back retainers: two straps across the back face
straps=box(-ox,-ih/2+4,z1,oxb,-ih/2+10,z1+2)+box(-ox,ih/2-14,z1,oxb,ih/2-8,z1+2)
# mounting flange (kept clear of the inlet end, where the plugs are)
fl=box(-17.5,-(ih/2+WALL+11.0),0,17.5,-2.0,FL_T)
body=snout+stop+sleeve+straps+fl
body=body-box(-iw/2,-ih/2,-1,iw/2,END0,SNOUT-1.5)        # keep the flange out of the duct (outlet stays open)
body=body+box(-iw/2,-1.0,0,iw/2,1.0,SNOUT)
body=body+box(-iw/2,-1.0,SNOUT-1.5,iw/2,1.0,SNOUT)      # divider continues to the face
# cable/board window check: nothing above y = ih/2 except the snout walls
for x,y in INSERTS: body=body-Manifold.cylinder(INS_D,INS/2,INS/2,32).translate([x,y,-0.01])
def board_parts(dy=0.0):
    sx=ST/2; z=SNOUT
    brd=box(sx+BRD_GAP,BRD_Y0,z-BRD_OVER,sx+BRD_GAP+BRD_T,SL/2+BRD_END,z+BRD_BACK)
    conn=box(sx,BRD_Y0+2,z+1,sx+BRD_GAP,SL/2-1,z+BRD_BACK-1)            # connector between face and board
    plugs=box(sx+BRD_GAP-1.5,BRD_Y0+0.5,z-BRD_OVER-PLUG_L,sx+BRD_GAP+BRD_T+2.5,SL/2-0.5,z-BRD_OVER)
    sensor=box(-ST/2,-SL/2,z,ST/2,SL/2,z+SD)
    return [m.translate([0,dy,0]) for m in (sensor,brd,conn,plugs)]
o=body.to_mesh(); t=trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
print('watertight',t.is_watertight,'bounds',t.bounds.round(1).tolist())
t.export('pms7003_cradle_v2.stl')
s=trimesh.Scene(); t2=t.copy(); t2.apply_translation([128-t2.bounds[:,0].mean(),128-t2.bounds[:,1].mean(),-t2.bounds[0,2]])
s.add_geometry(t2,node_name='pms7003_cradle',geom_name='pms7003_cradle'); s.export('pms7003_cradle.3mf')
import numpy as np
worst=max(sum((m^body).volume() for m in board_parts(d)) for d in np.linspace(0,40,81))
print('sensor+board+plugs overlap with cradle over the slide-in path: %.3f mm3'%worst)
print('insert positions (relative to sensor centre):',INSERTS)
