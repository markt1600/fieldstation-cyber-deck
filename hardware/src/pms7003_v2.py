"""PMS7003 cradle with a ducted snout. Local coords: x across the 12 mm face, y along the 48 mm face (y+ = inlet end,
where the adapter board and Dupont plugs are), z = 0 at the panel back, + into the case."""
import trimesh
from manifold3d import Manifold
SL,ST,SD=48.0,12.0,37.0; CL=0.4
iw,ih=ST+CL,SL+CL                 # x, y interior
SNOUT=34.0                        # sensor face sits this far behind the panel (room for the Dupont plugs + wire bend)
WALL=2.0; LIP=1.2; FL_T=7.0
# Adapter board (measured): lies flat on the +x (label) face, 3.5 mm above it, 1.6 thick; reaches 12.77 mm back
# from the inlet face, overhangs the inlet face by 6.5 mm and the board end by 9 mm. Header pins run back down
# to the Dupont plugs, which sit mid-thickness in front of the inlet face, pointing at the panel, over y ~12..23.
BRD_GAP,BRD_T=3.5,1.6; BRD_BACK,BRD_OVER,BRD_END=12.77,6.5,9.0; BRD_Y0=12.0; PLUG_L=19.0
WALL_B=1.2                       # thinner wall on the board side
INS=4.0; INS_D=6.0
INSERTS=[(-13.0,-12.0),(13.0,-12.0),(0.0,-(ih/2+WALL+6.0))]
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
ox,oy=iw/2+WALL,ih/2+WALL; oxb=iw/2+WALL_B   # -x side, +x (board) side
# Measured on the sensor face, from the board end: inlet slot 4.73..14.85 mm, outlet starts 30.45 mm.
# Sensor spans y -24..+24 with the board end at +24, so: inlet y +9.15..+19.27, outlet y < -6.45.
# The Dupont plugs sit in front of the same face, mid-thickness, beside the inlet, pointing at the panel.
# So the inlet chamber takes in the whole board end (inlet + plugs); the wires leave through a slot in its end wall.
END0=ih/2                      # inner face of the inlet chamber's end wall (just past the sensor's end)
END1=END0+2.0
PIN_Z=7.5                      # header pins run from the board to the plugs within this much of the face
# snout: two chambers (outlet / inlet+plugs) split by a rib, open at the panel end
snout=box(-ox,-oy,0,oxb,END1,SNOUT)-box(-iw/2,-ih/2,-1,iw/2,END0,SNOUT+1)
# face stop: lip at the back of the snout on the long sides and the outlet end (none at the plug end)
stop=box(-ox,-oy,SNOUT-1.5,oxb,END1,SNOUT)-box(-iw/2+LIP,-ih/2+LIP,SNOUT-2,iw/2-LIP,END1+1,SNOUT+1)
# sleeve behind: open at the back so the sensor drops in face-first from behind, plugs leading
z0,z1=SNOUT,SNOUT+SD+CL
sleeve=box(-ox,-oy,z0,oxb,ih/2,z1)-box(-iw/2,-ih/2,z0-1,iw/2,ih/2+1,z1+1)
# board side: open the wall where the connector, board and header pins pass (y > BRD_Y0-2), full length
sleeve=sleeve-box(iw/2-0.5,BRD_Y0-2.0,z0-1,oxb+1,ih/2+5,z1+1)
snout=snout-box(iw/2-0.5,BRD_Y0-2.0,SNOUT-PIN_Z,oxb+1,END1+1,SNOUT+1)     # pin notch, packed with foam after
stop=stop-box(iw/2-LIP-0.5,BRD_Y0-2.0,SNOUT-PIN_Z,oxb+1,END1+1,SNOUT+1)
# wire slot through the inlet chamber's end wall, open to the back so the wires slide in with the sensor
WS_X,WS_Z=3.5,4.0
snout=snout-box(-WS_X,END0-1,WS_Z,WS_X,END1+1,SNOUT+1); stop=stop-box(-WS_X,END0-1,WS_Z,WS_X,END1+1,SNOUT+1)
# zip-tie guides: pairs of ridges round the sleeve, a cable tie over the sensor's back holds it in
zt=None
for yc in (-14.0,6.0):
    for dy in (-3.0,3.0):
        r=box(-ox-1,yc+dy-0.6,z1-12,-ox,yc+dy+0.6,z1)+box(oxb,yc+dy-0.6,z1-12,oxb+1,yc+dy+0.6,z1)
        zt=r if zt is None else zt+r
fl=box(-17.5,-(ih/2+WALL+11.0),0,17.5,-2.0,FL_T)
body=snout+stop+sleeve+zt+fl
body=body-box(-iw/2,-ih/2,-1,iw/2,END0,SNOUT-1.5)        # keep the flange out of the outlet chamber
body=body+box(-iw/2,-1.0,0,iw/2,1.0,SNOUT)                # divider rib, panel to sensor face
# cable/board window check: nothing above y = ih/2 except the snout walls
for x,y in INSERTS: body=body-Manifold.cylinder(INS_D,INS/2,INS/2,32).translate([x,y,-0.01])
def board_parts(dz=0.0):
    sx=ST/2; z=SNOUT
    brd=box(sx+BRD_GAP,BRD_Y0,z-BRD_OVER,sx+BRD_GAP+BRD_T,SL/2+BRD_END,z+BRD_BACK)
    conn=box(sx,BRD_Y0+2,z+1,sx+BRD_GAP,SL/2-1,z+BRD_BACK-1)            # connector between face and board
    plugs=box(-2.5,BRD_Y0+0.5,z-1-PLUG_L,2.5,SL/2-0.5,z-1)              # mid-thickness, facing the panel
    pins=box(0,BRD_Y0+0.5,z-PIN_Z+1,sx+BRD_GAP,SL/2-0.5,z-2)           # header pins from the board down to the plugs
    sensor=box(-ST/2,-SL/2,z,ST/2,SL/2,z+SD)
    return [m.translate([0,0,dz]) for m in (sensor,brd,conn,plugs+pins)]
o=body.to_mesh(); t=trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
print('watertight',t.is_watertight,'bounds',t.bounds.round(1).tolist())
t.export('pms7003_cradle_v2.stl')
s=trimesh.Scene(); t2=t.copy(); t2.apply_translation([128-t2.bounds[:,0].mean(),128-t2.bounds[:,1].mean(),-t2.bounds[0,2]])
s.add_geometry(t2,node_name='pms7003_cradle',geom_name='pms7003_cradle'); s.export('pms7003_cradle.3mf')
import numpy as np
worst=max(sum((m^body).volume() for m in board_parts(d)) for d in np.linspace(0,70,141))
print('sensor+board+plugs overlap with cradle as it drops in from behind: %.3f mm3'%worst)
print('insert positions (relative to sensor centre):',INSERTS)
