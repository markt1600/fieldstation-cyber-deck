"""PMS7003 cradle with a ducted snout. Local coords: x across the 12 mm face, y along the 48 mm face (y+ = inlet end,
where the adapter board and Dupont plugs are), z = 0 at the panel back, + into the case."""
import trimesh
from manifold3d import Manifold
SL,ST,SD=48.0,12.0,37.0; CL=0.4
iw,ih=ST+CL,SL+CL                 # x, y interior
SNOUT=26.0                        # sensor face sits this far behind the panel (plug clearance)
WALL=2.0; LIP=1.2; FL_T=7.0
BOARD_EXT=16.0                    # adapter board beyond the sensor's inlet end (assumed)
INS=4.0; INS_D=6.0
INSERTS=[(-13.0,-12.0),(13.0,-12.0),(0.0,-(ih/2+WALL+6.0))]
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
ox,oy=iw/2+WALL,ih/2+WALL
# Measured on the sensor face, from the board end: inlet slot 4.73..14.85 mm, outlet starts 30.45 mm.
# Sensor spans y -24..+24 with the board end at +24, so: inlet y +9.15..+19.27, outlet y < -6.45.
INLET_NEAR=24.0-4.73
END0=INLET_NEAR+1.0            # inner face of the duct's end wall (1 mm clear of the inlet slot)
END1=END0+3.0                  # wall is 3 mm thick and lands on the sensor face, short of its end,
                               # so the area beyond the sensor's end stays open for the board and Dupont plugs
# snout duct, open both ends, with a divider rib between inlet and outlet
snout=box(-ox,-oy,0,ox,END1,SNOUT)-box(-iw/2,-ih/2,-1,iw/2,END0,SNOUT+1)
snout=snout+box(-iw/2,-1.0,0,iw/2,1.0,SNOUT)
# face stop: lip at the back of the snout; the sensor face (with a foam gasket) presses on it all round
stop=box(-ox,-oy,SNOUT-1.5,ox,END1,SNOUT)-box(-iw/2+LIP,-ih/2+LIP,SNOUT-2,iw/2-LIP,END0,SNOUT+1)
# sleeve behind: long sides + closed outlet end; inlet end open so the adapter board can plug on
z0,z1=SNOUT,SNOUT+SD+CL
sleeve=box(-ox,-oy,z0,ox,23.0,z1)-box(-iw/2,-ih/2,z0-1,iw/2,ih/2+1,z1+1)   # side walls stop 1 mm short of the board end
# back retainers: two straps across the back face
straps=box(-ox,-ih/2+4,z1,ox,-ih/2+10,z1+2)+box(-ox,ih/2-14,z1,ox,ih/2-8,z1+2)
# mounting flange (kept clear of the inlet end, where the plugs are)
fl=box(-17.5,-(ih/2+WALL+11.0),0,17.5,-2.0,FL_T)
body=snout+stop+sleeve+straps+fl
body=body+box(-iw/2,-1.0,SNOUT-1.5,iw/2,1.0,SNOUT)      # divider continues to the face
# cable/board window check: nothing above y = ih/2 except the snout walls
for x,y in INSERTS: body=body-Manifold.cylinder(INS_D,INS/2,INS/2,32).translate([x,y,-0.01])
o=body.to_mesh(); t=trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
print('watertight',t.is_watertight,'bounds',t.bounds.round(1).tolist())
t.export('pms7003_cradle_v2.stl')
s=trimesh.Scene(); t2=t.copy(); t2.apply_translation([128-t2.bounds[:,0].mean(),128-t2.bounds[:,1].mean(),-t2.bounds[0,2]])
s.add_geometry(t2,node_name='pms7003_cradle',geom_name='pms7003_cradle'); s.export('pms7003_cradle.3mf')
print('insert positions (relative to sensor centre):',INSERTS)
