"""Builds every printable part straight from the manifold models (no vertex merging) and lays out the P1S plates."""
import numpy as np, trimesh, math
def ns(fn, stop=None):
    src=open(fn).read()
    if stop: src=src.split(stop)[0]
    g={'__name__':'lib'}; exec(src,g); return g
F=ns('frame.py')
L=ns('lid.py')
P=ns('pod.py',"def save(")
C=ns('screen_clamp.py',"# print lip-side down")
S=ns('pms7003_v2.py',"o=body.to_mesh()")
K=ns('kickstand.py',"def tm(m)")
from manifold3d import Manifold
def tm(m):
    o=m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
parts={}
# The base is modelled in panel coordinates (x right and y up as seen from the front, z away from you into the case),
# which is a left-handed frame. Every base part must be reflected once on export or it prints as a mirror image.
full,pl,pr=F['build_panel'](); parts['base_panel_L']=tm(pl.mirror([0,0,1])); parts['base_panel_R']=tm(pr.mirror([0,0,1]))   # back face on the bed, front face up
parts['port_tray']=tm(F['build_tray']().mirror([0,0,1]))
for n in F['POSTS']: parts['post_'+n]=tm(F['build_post'](n))
cr=L['build_cradle'](); ov=L['build_overlay']()
cl,crr=L['split'](cr,L['CRADLE_H'],L['CRADLE_TABS']); ol,orr=L['split'](ov,L['OT'],L['OVERLAY_TABS']); ol=L['stretch_left'](ol)
parts['kb_door']=tm(L['build_door']());   # outside face up, magnet pockets open on the bed side
parts['kb_cradle_L']=tm(cl); parts['kb_cradle_R']=tm(crr); parts['kb_overlay_L']=tm(ol.mirror([0,0,1])); parts['kb_overlay_R']=tm(orr.mirror([0,0,1]))
for s in ('L','R'): parts['pod_body_'+s]=tm(P['body']); parts['pod_baffle_'+s]=tm(P['baf'])
clamp=C['c'].mirror([0,0,1]).translate([0,0,C['H']])
for i in range(1,5): parts[f'screen_clamp_{i}']=tm(clamp)
parts['pms7003_cradle']=tm(S['body'])   # placed mirrored in the base (board toward the screen); that mirror and the export reflection cancel
parts['panel_splice']=tm(Manifold.cube([40,10,2]))
parts['kvm_spacer']=tm(Manifold.cube([60,60,2.0]))   # VHB both sides: KVM to the back of the screen
FPm=ns('floorplate.py'); parts['floor_plate']=tm(FPm['build_floor_plate']().mirror([0,0,1]))   # glued face down
for s in ('L','R'):
    parts['stand_plate_'+s]=tm(K['plate'])
    parts['stand_leg_'+s]=tm(K['leg'].rotate([0,90,0]))
bad=[n for n,t in parts.items() if not t.is_watertight]
print('parts',len(parts),'non-watertight:',bad)
M=3.0
def plate(fn,items):
    s=trimesh.Scene(); bb=[]
    for name,x,y,rot in items:
        t=parts[name].copy()
        if rot: t.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rot),[0,0,1]))
        t.apply_translation([x-t.bounds[0,0],y-t.bounds[0,1],-t.bounds[0,2]]); bb.append((name,t.bounds))
        assert t.bounds[0,0]>=2.9 and t.bounds[0,1]>=2.9 and t.bounds[1,0]<=253.1 and t.bounds[1,1]<=253.1,(fn,name,t.bounds.round(1))
        s.add_geometry(t,node_name=name,geom_name=name)
    for i in range(len(bb)):
        for j in range(i+1,len(bb)):
            a,b=bb[i][1],bb[j][1]
            assert a[1,0]+2<=b[0,0] or b[1,0]+2<=a[0,0] or a[1,1]+2<=b[0,1] or b[1,1]+2<=a[0,1],(fn,bb[i][0],bb[j][0])
    s.export('../print/'+fn)
    w=sum(abs(parts[n].volume) for n,*_ in items)/1000
    print(f'{fn}: {len(items)} parts, tallest {max(b[1,2] for _,b in bb):.1f} mm, solid {w:.0f} cm3')
w=lambda n:parts[n].extents[0]; h=lambda n:parts[n].extents[1]
def centred(n): return (128-w(n)/2,128-h(n)/2)
for fn,n in [('K1_keyboard_cradle_left.3mf','kb_cradle_L'),('K2_keyboard_cradle_right.3mf','kb_cradle_R'),
             ('K3_keyboard_overlay_left.3mf','kb_overlay_L')]:
    plate(fn,[(n,*centred(n),0)])
plate('K4_keyboard_overlay_right_+_tray_door.3mf',[('kb_overlay_R',M,M+12,0),('kb_door',M+w('kb_overlay_R')+8,M+40,90)])
x2=M+w('base_panel_L')+6
plate('B1_base_panel_left_+_baffles.3mf',[('base_panel_L',M,M+12,0),('pod_baffle_L',x2,M+20,0),('pod_baffle_R',x2,M+20+h('pod_baffle_L')+8,0),('panel_splice',x2+20,M+20+2*h('pod_baffle_L')+20,90)])
x2=M+w('base_panel_R')+6
plate('B2_base_panel_right_+_pod_bodies.3mf',[('base_panel_R',M,M+12,0),('pod_body_L',x2,M+20,0),('pod_body_R',x2,M+20+h('pod_body_L')+8,0)])
pw=w('post_TL'); cw=w('screen_clamp_1')
items=[('port_tray',M+5,M+5,0)]
ty=M+5+h('port_tray')+10
for i,n in enumerate(['post_TL','post_TR','post_ML','post_MR']): items.append((n,M+5+i*(pw+8),ty,0))
cx=M+5+w('port_tray')+12
for i in range(4): items.append((f'screen_clamp_{i+1}',cx+(i%2)*(cw+6),M+5+(i//2)*(cw+6),0))
items.append(('pms7003_cradle',cx+12,M+5+2*(cw+6)+8,0))
plate('B3_tray_posts_clamps_sensor.3mf',items)
plate('B4_kickstands.3mf',[('stand_plate_L',20,20,0),('stand_plate_R',90,20,0),('stand_leg_L',20,110,0),('stand_leg_R',50,110,0)])

# both complete speaker pods (2 bodies + 2 baffles) on one plate
c=128
plate('speaker_pods_complete_x2.3mf',[('pod_body_L',c-85,c+5,0),('pod_body_R',c+5,c+5,0),('pod_baffle_L',c-85,c-85,0),('pod_baffle_R',c+5,c-85,0)])

# port tray on its own, for printing ahead of the rest of B3
plate('B3a_port_tray_and_sensor.3mf',[('port_tray',M+20,M+60,0),('pms7003_cradle',M+20+w('port_tray')+25,M+60,0)])

# floor plate on its own (Pi pocket, perfboard bosses; breakout bosses to come)
plate('B5_floor_plate.3mf',[('floor_plate',10,70,0),('kvm_spacer',28,4,0)])

# panel halves on their own (pods and baffles already printed); the seam splice strip rides with the left half
plate('B1p_base_panel_left_only.3mf',[('base_panel_L',M,M+12,0),('panel_splice',M+w('base_panel_L')+10,M+20,90)])
plate('B2p_base_panel_right_+_tray_door.3mf',[('base_panel_R',M,M+12,0),('kb_door',M+w('base_panel_R')+12,M+40,90)])

# posts and screen clamps on their own (tray and sensor cradle printed separately); brim recommended for the posts
items=[]
for i,n in enumerate(['post_TL','post_TR','post_ML','post_MR']): items.append((n,M+20+i*(pw+14),M+20,0))
cx=M+20
for i in range(4): items.append((f'screen_clamp_{i+1}',cx+i*(cw+10),M+20+h('post_TL')+20,0))
plate('B3p_posts_and_screen_clamps.3mf',items)
