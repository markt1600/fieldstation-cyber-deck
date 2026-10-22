import numpy as np, trimesh, math, time
from manifold3d import Manifold
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from raster import render
def ns(fn,stop=None):
    src=open(fn).read(); src=src.split(stop)[0] if stop else src
    g={'__name__':'lib'}; exec(src,g); return g
F=ns('frame.py'); LID=ns('lid.py'); P=ns('pod.py',"def save("); C=ns('screen_clamp.py',"# print lip-side down"); S=ns('pms7003_v2.py',"o=body.to_mesh()"); K=ns('kickstand.py',"def tm(m)")
def tm(m):
    o=m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
def T(m,dx=0,dy=0,dz=0):
    m=m.copy(); m.apply_translation([dx,dy,dz]); return m
def cyl(r,h,seg=24): return trimesh.creation.cylinder(radius=r,height=h,sections=seg)
def csk_screw(L=20.0,d=3.0):     # countersunk screw, head at z=0 pointing +z... built along -z from the head top
    head=trimesh.creation.cone(radius=d,height=d*0.6,sections=24); head.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0])); head.apply_translation([0,0,0])
    shaft=cyl(d/2,L-d*0.6); shaft.apply_translation([0,0,-(d*0.6)-(L-d*0.6)/2])
    hd=trimesh.creation.cylinder(radius=d,height=0.3,sections=24); hd.apply_translation([0,0,-0.15])
    return trimesh.util.concatenate([hd,shaft,T(head,0,0,0)])
def insert(): return cyl(2.3,5.7,16)
def cube(s): return trimesh.creation.box([s,s,s])
STEEL=(0.72,0.74,0.77); BRASS=(0.80,0.63,0.28); MAG=(0.55,0.57,0.62); PLA=(0.62,0.66,0.70); DARK=(0.20,0.22,0.24); FOAM=(0.95,0.78,0.35); BLUE=(0.25,0.45,0.75)
sheets=[]
# ---------------- A: speaker pod (vertical stack, front of the pod facing up) ----------------
t0=time.time()
BD,B,R=P['BODY_D'],P['BAFFLE'],P['RIM']
items=[]; labels=[]
body=tm(P['body']); items.append((body,PLA)); labels.append(('Pod body',[ -40,-40,BD*0.5]))
for sx in (-1,1):
    for sy in (-1,1):
        items.append((T(insert(),sx*36,sy*36,BD-2.85+12),BRASS))
labels.append(('M3 heat-set insert ×4',[36,-36,BD+12]))
for mx,my in P['MAGS']: items.append((T(cube(4.56),mx,my,BD+22),MAG)); items.append((T(cube(4.56),mx,my,BD+30),MAG))
labels.append(('Magnet cubes ×8 (4 + 4)',[P['MAGS'][2][0],P['MAGS'][2][1],BD+26]))
zb=BD+45
items.append((T(tm(P['baf']),0,0,zb),PLA)); labels.append(('Baffle (magnets inside)',[40,40,zb+8]))
# driver: frame + surround + cone + basket + magnet
zd=zb+B+R+28
fr=tm(F['rrect'](64.5,57.2,6,0,0).__class__.square([57.2,57.2],center=True).offset(4,F['JoinType'].Round,circular_segments=24).extrude(3.0) if False else Manifold.cube([57.2,57.2,3],center=True))
drv=[(T(fr,0,0,zd),DARK),(T(cyl(26,4,48),0,0,zd+2.5),(0.12,0.12,0.13)),(T(cyl(19,6,48),0,0,zd+3),(0.10,0.10,0.11)),
     (T(trimesh.creation.cone(radius=24,height=22,sections=40).apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0])) or cyl(1,1),0,0,zd-1.5),DARK) if False else (T(cyl(22,14,40),0,0,zd-8.5),DARK),
     (T(cyl(16,22,40),0,0,zd-26),(0.78,0.80,0.83)),(T(trimesh.creation.box([31.2,6,10]),0,30,zd-6),(0.92,0.92,0.88))]
items+=drv; labels.append(('ND65-4 driver (terminal block into the notch)',[0,-32,zd]))
for sx in (-1,1):
    for sy in (-1,1): items.append((T(cyl(2.1,9.5,16),sx*23.25,sy*23.25,zd+20),STEEL)); items.append((T(cyl(3.8,1.6,16),sx*23.25,sy*23.25,zd+25.5),STEEL))
labels.append(('#8 × 3/8" pan screws ×4',[23.25,23.25,zd+26]))
zg=zd+48
g=Manifold.extrude(F['rrect'](80,80,4,0,0)-F['rrect'](66.4,66.4,4,0,0),1.5)
items.append((T(tm(g),0,0,zg),FOAM)); labels.append(('Foam gasket on the rim face',[-40,0,zg]))
# panel piece around the pod
cx,cy=F['PODS'][0]
full,_,_=F['build_panel']()
piece=(full^Manifold.cube([96,96,10]).translate([cx-48,cy-48,-3])).translate([-cx,-cy,0]).mirror([0,0,1])
zp=zg+24
items.append((T(tm(piece),0,0,zp+F['T']),(0.30,0.33,0.36))); labels.append(('Front panel (grille)',[-48,-40,zp+4]))
for sx in (-1,1):
    for sy in (-1,1): items.append((T(csk_screw(20),sx*36,sy*36,zp+F['T']+22),STEEL))
labels.append(('M3 × 20 countersunk ×4, from the front',[36,36,zp+F['T']+22]))
guides=[([sx*36,sy*36,BD],[sx*36,sy*36,zp+F['T']+22]) for sx in (-1,1) for sy in (-1,1)]
sheets.append(('A  Speaker pod  (×2)',items,labels,guides,(1.1,-1.35,0.75),False))
# ---------------- B: base panel (front face down, parts attach to the back) ----------------
items=[];labels=[];guides=[]
full=tm(F['build_panel']()[0]); items.append((full,(0.30,0.33,0.36))); labels.append(('Base panel (2 halves, epoxied)',[20,-5,0]))
def Bz(m,dz): return T(m,0,0,dz)
# screen case + clamps
sc=trimesh.creation.box([F['SC_W'],F['SC_H'],F['SC_T']]); sc.apply_translation([F['SC_CX'],F['SC_CY'],F['T']+F['SC_T']/2+40]); items.append((sc,(0.10,0.12,0.16))); labels.append(('7" screen (in its case)',[F['SC_CX'],F['SC_CY']+40,F['T']+57]))
clamp=tm(C['c'])
for (x,y,sx,sy) in [(F['SC_X0'],F['SC_Y0'],1,1),(F['SC_X0']+F['SC_W'],F['SC_Y0'],-1,1),(F['SC_X0'],F['SC_Y0']+F['SC_H'],1,-1),(F['SC_X0']+F['SC_W'],F['SC_Y0']+F['SC_H'],-1,-1)]:
    c=clamp.copy(); c.apply_scale([sx,sy,1]); c.apply_translation([x,y,F['T']+70]); items.append((c,PLA))
labels.append(('Screen clamps ×4',[F['SC_X0']+F['SC_W'],F['SC_Y0'],F['T']+80]))
for x,y in F['clamp_holes'](): guides.append(([x,y,0],[x,y,F['T']+70]))
tray=tm(F['build_tray']().translate([0,0,30])); items.append((tray,PLA)); labels.append(('Port tray',[F['PK_CX'],F['PK_CY']-40,F['T']+30]))
for x,y in F['TRAY_INS']: guides.append(([x,y,0],[x,y,F['T']+30]))
pod=trimesh.util.concatenate([tm(P['body']).apply_transform(np.eye(4)),T(tm(P['baf']),0,0,BD)])
for i,(px,py) in enumerate(F['PODS']):
    pm=pod.copy(); pm.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0])); pm.apply_translation([px,py,F['T']+78+70]); items.append((pm,PLA))
    for sx in (-1,1):
        for sy in (-1,1): guides.append(([px+sx*36,py+sy*36,0],[px+sx*36,py+sy*36,F['T']+70]))
labels.append(('Speaker pods ×2',[F['PODS'][1][0],F['PODS'][1][1]-40,F['T']+150]))
pms=tm(S['body'].mirror([1,0,0])); pms.apply_translation([F['AIR_C'][0],F['AIR_C'][1],F['T']+45]); items.append((pms,BLUE)); labels.append(('PMS7003 cradle',[F['AIR_C'][0],F['AIR_C'][1]+30,F['T']+110]))
for nme,(x,y) in F['POSTS'].items():
    p=tm(F['build_post'](nme)); p.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0])); p.apply_translation([0,2*y,F['T']+F['POST_H']+120]); items.append((p,PLA)); guides.append(([x,y,0],[x,y,F['T']+120]))
labels.append(('Floor posts ×4 (VHB feet)',[F['POSTS']['TR'][0],F['POSTS']['TR'][1],F['T']+210]))
sheets.append(('B  Base panel: everything screws in from the front',items,labels,guides,(0.9,-1.6,1.9),True))
# ---------------- C: keyboard lid ----------------
items=[];labels=[];guides=[]
cr=tm(LID['build_cradle']()); items.append((cr,PLA)); labels.append(('Keyboard cradle (VHB to lid floor)',[20,20,5]))
kb=trimesh.creation.box([LID['KB_W'],LID['KB_D'],8]); kb.apply_translation([LID['PW']/2,(LID['KY0']+LID['KY1'])/2,LID['PLATE_Z']+40]); items.append((kb,(0.80,0.82,0.85))); labels.append(('Keyboard',[LID['KX0'],LID['KY0'],LID['PLATE_Z']+40]))
ov=tm(LID['build_overlay']()); ov.apply_translation([0,0,LID['PLATE_Z']+80]); items.append((ov,(0.30,0.33,0.36))); labels.append(('Overlay (2 halves, epoxied)',[0,120,LID['PLATE_Z']+82]))
dr=tm(LID['build_door']()); dr.apply_translation([0,0,LID['PLATE_Z']+110]); items.append((dr,(0.36,0.39,0.42))); labels.append(('Tray door (magnets)',[(LID['DOOR_X0']+LID['DOOR_X1'])/2,LID['DOOR_Y1'],LID['PLATE_Z']+112]))
for x,y in LID['insert_points']():
    items.append((T(csk_screw(8),x,y,LID['PLATE_Z']+95),STEEL)); guides.append(([x,y,LID['CRADLE_H']],[x,y,LID['PLATE_Z']+95]))
labels.append(('M3 × 8 countersunk ×12',[LID['insert_points']()[-1][0],LID['insert_points']()[-1][1],LID['PLATE_Z']+95]))
sheets.append(('C  Keyboard lid',items,labels,guides,(0.8,-1.5,1.4),False))
# ---------------- D: kickstand ----------------
items=[];labels=[];guides=[]
pl=tm(K['plate']); items.append((pl,PLA)); labels.append(('Hinge plate (glued to case back)',[-25,30,1]))
lg=K['leg'].transform(np.asarray(trimesh.transformations.rotation_matrix(math.radians(180-K['ALPHA']),[1,0,0],[0,0,K['H_P']])[:3,:]))
items.append((tm(lg),PLA)); labels.append(('Leg (shown open, 15° lean)',[0,-60,60]))
bolt=cyl(2.0,40,16); bolt.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0])); bolt.apply_translation([-55,0,K['H_P']]); items.append((bolt,STEEL))
hd=cyl(3.5,3,6); hd.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0])); hd.apply_translation([-76.5,0,K['H_P']]); items.append((hd,STEEL))
nut=cyl(3.9,4,6); nut.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0])); nut.apply_translation([45,0,K['H_P']]); items.append((nut,STEEL))
labels.append(('M4 × 40 bolt',[-70,0,K['H_P']+4])); labels.append(('M4 nyloc nut',[45,0,K['H_P']+5]))
guides.append(([-78,0,K['H_P']],[50,0,K['H_P']]))
sheets.append(('D  Kickstand  (×2)',items,labels,guides,(1.4,-0.9,0.8),False))
print('built %.1fs'%(time.time()-t0))
# ---------------- render ----------------
fig=plt.figure(figsize=(16,20),dpi=100)
pos=[[0.02,0.50,0.47,0.47],[0.51,0.50,0.47,0.47],[0.02,0.06,0.47,0.42],[0.51,0.06,0.47,0.42]]
for (title,items,labels,guides,view,lh),p in zip(sheets,pos):
    t0=time.time(); img,proj=render(items,view=view,W=1100,H=1000,lh=lh)
    ax=fig.add_axes(p); ax.imshow(img); ax.set_axis_off(); ax.set_title(title,fontsize=15,loc='left',fontweight='bold',color='#1d2124')
    for a,b in guides:
        q=proj(np.array([a,b])); ax.plot(q[:,0],q[:,1],ls=(0,(4,3)),lw=0.9,color='#2f6e8f',alpha=0.8)
    for txt,pt in labels:
        q=proj(np.array(pt))[0]
        left=q[0]>img.shape[1]*0.55
        ax.annotate(txt,xy=q,xytext=(q[0]-40 if left else q[0]+50,q[1]-30),ha='right' if left else 'left',fontsize=10,color='#1d2124',arrowprops=dict(arrowstyle='-',lw=0.7,color='#555'),bbox=dict(fc='white',ec='#c9cdd2',lw=0.6,pad=2.5))
    print(title,'%.1fs'%(time.time()-t0))
hw=("HARDWARE\n"
    "M3 heat-set inserts ×50  ·  M3×8 countersunk ×24 (lid, clamps, tray, sensor)  ·  M3×10 countersunk ×4 (posts)  ·  M3×20 countersunk ×8 (pods)\n"
    "#8×3/8\" pan self-tappers ×8 (drivers)  ·  M4×40 bolt + nyloc ×2 (kickstands)  ·  M3×10 bolt + nut ×6 (USB flanges)  ·  4.56 mm magnet cubes ×24\n"
    "Foam gasket tape  ·  VHB tape  ·  epoxy (dovetails)  ·  Loctite 770 primer + 406 (kickstands to the polypropylene case)")
fig.text(0.02,0.015,hw,fontsize=11,color='#1d2124',family='monospace',linespacing=1.5)
fig.text(0.02,0.985,'FIELDSTATION — assembly',fontsize=20,fontweight='bold',color='#1d2124',va='top')
fig.text(0.02,0.968,'Dashed lines = screw axes. All panel and overlay screws go in from the front face.',fontsize=11,color='#555',va='top')
plt.savefig('../docs/assembly_sheet.png',facecolor='white')
print('saved')
