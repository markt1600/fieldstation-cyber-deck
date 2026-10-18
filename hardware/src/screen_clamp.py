import trimesh
from manifold3d import Manifold
T=16.8+0.4        # case thickness + clearance (take up with foam tape)
LIP=2.5; OVER=6.0 # lip thickness, overlap onto case back
WALL=9.0; ARM=24.0
INS=4.0; INS_D=6.0
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
# case corner at origin, case occupies x>0,y>0, panel back face at z=0
H=T+LIP
c=box(-WALL,-WALL,0,ARM,0,H)+box(-WALL,-WALL,0,0,ARM,H)          # walls along both edges
c=c+box(0,0,T,ARM,OVER,H)+box(0,0,T,OVER,ARM,H)                    # L lip over case back
c=c-Manifold.cylinder(H+2,1.0,1.0,24).translate([0,0,-1])          # corner relief
for x,y in [(-WALL/2,ARM-8),(ARM-8,-WALL/2)]:
    c=c-Manifold.cylinder(INS_D,INS/2,INS/2,32).translate([x,y,-0.01])   # M3 heat-set from panel side
# print lip-side down: flip
c=c.mirror([0,0,1]).translate([0,0,H])
m=c.to_mesh(); t=trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts,process=False)
print('watertight',t.is_watertight,'bbox',t.bounds.round(1).tolist())
s=trimesh.Scene()
for i,(x,y) in enumerate([(90,90),(150,90),(90,150),(150,150)]):
    p=t.copy(); p.apply_translation([x-p.bounds[:,0].mean(),y-p.bounds[:,1].mean(),-p.bounds[0,2]])
    s.add_geometry(p,node_name=f'screen_clamp_{i+1}',geom_name=f'screen_clamp_{i+1}')
s.export('screen_clamps_x4.3mf'); print('3mf parts',len(trimesh.load('screen_clamps_x4.3mf').geometry))
