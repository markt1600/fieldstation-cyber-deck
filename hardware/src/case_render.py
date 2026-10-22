"""Renders ../docs/case_assembly.png: the base of the Peli 1400 with everything in place (top wall cut away),
and the same parts exploded front-to-back in assembly order."""
import numpy as np, trimesh, math, time
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from manifold3d import Manifold
from raster import render
def ns(fn,stop=None):
    src=open(fn).read(); src=src.split(stop)[0] if stop else src
    g={'__name__':'lib'}; exec(src,g); return g
F=ns('frame.py'); P=ns('pod.py',"def save("); C=ns('screen_clamp.py',"# print lip-side down")
S=ns('pms7003_v2.py',"o=body.to_mesh()"); FP=ns('floorplate.py',"if __name__")
T=F['T']; PW,PH=F['PW'],F['PH']; FLOOR_Z=F['BASE_DEPTH']-F['RIM_DROP']
def tm(m):
    o=m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
PLA=(0.62,0.66,0.70); PANEL=(0.30,0.33,0.36); CASE=(0.20,0.36,0.30); SCREEN=(0.10,0.12,0.16); PCB=(0.16,0.50,0.28)
PI=(0.83,0.20,0.25); KVM=(0.15,0.15,0.17); BRASS=(0.80,0.63,0.28); SENSOR=(0.25,0.55,0.72); FOAM=(0.95,0.78,0.35)

parts={}   # name -> (manifold or trimesh in panel coords, colour, explode group)
parts['Base panel']=(F['build_panel']()[0],PANEL,0)
parts['Screen (7" in case)']=(box(F['SC_X0'],F['SC_Y0'],T,F['SC_X0']+F['SC_W'],F['SC_Y0']+F['SC_H'],T+F['SC_T']),SCREEN,1)
clamp=C['c']
cl=None
for (x,y,sx,sy) in [(F['SC_X0'],F['SC_Y0'],1,1),(F['SC_X0']+F['SC_W'],F['SC_Y0'],-1,1),(F['SC_X0'],F['SC_Y0']+F['SC_H'],1,-1),(F['SC_X0']+F['SC_W'],F['SC_Y0']+F['SC_H'],-1,-1)]:
    c=clamp.scale([sx,sy,1]).translate([x,y,T]); cl=c if cl is None else cl+c
parts['Screen clamps ×4']=(cl,PLA,2)
parts['Port tray']=(F['build_tray'](),PLA,1)
pod=P['body']+P['baf'].translate([0,0,P['BODY_D']])
pb=tm(pod).bounds; ph=pb[1][2]-pb[0][2]
pd=None
for px,py in F['PODS']:
    m=pod.mirror([0,0,1]).translate([px,py,T+ph+pb[0][2]]); pd=m if pd is None else pd+m
parts['Speaker pods ×2']=(pd,PLA,1)
sens=None
for m in S['board_parts']():
    sens=m if sens is None else sens+m
mv=lambda m: m.mirror([1,0,0]).translate([F['AIR_C'][0],F['AIR_C'][1],T])
parts['PMS7003 cradle']=(mv(S['body']),(0.95,0.62,0.25),1)
parts['PMS7003 + adapter board']=(mv(sens),SENSOR,1)
po=None
for n in F['POSTS']:
    m=F['build_post'](n).mirror([0,0,1]).translate([0,0,FLOOR_Z-F['VHB']]); po=m if po is None else po+m
parts['Floor posts ×4']=(po,PLA,3)
parts['KVM spacer (VHB both sides)']=(box(67,125,T+F['SC_T']+1.1,127,185,T+F['SC_T']+3.1),FOAM,4)
kvm=box(42,114,25,139,205,48)
for x in (70,82,100,112): kvm=kvm+Manifold.cylinder(18,3.2,3.2,16).rotate([90,0,0]).translate([x,114,36.5])   # host cables (stubs)
parts['KVM (C2-H46)']=(kvm,KVM,5)
parts['Pi 5 in X1202 case']=(box(145,105,FLOOR_Z-3-62.75,145+98.75,105+90.2,FLOOR_Z-3),PI,6)
bo=FP['BO']; zb=FLOOR_Z-3-FP['BO_BOSS_H']
brk=box(bo[0],bo[1],zb-1.6,bo[2],bo[3],zb)+box(bo[0]+3,bo[1]+3,zb-1.6-10,bo[0]+11,bo[3]-3,zb-1.6)+box(bo[2]-11,bo[1]+3,zb-1.6-10,bo[2]-3,bo[3]-3,zb-1.6)+box(bo[0]+18,bo[3]-12,zb-1.6-9,bo[2]-18,bo[3]-4,zb-1.6)
parts['GPIO breakout (turned 90°)']=(brk,PCB,7)
pbd=FP['PB']; zp=FLOOR_Z-3-FP['BOSS_H']
parts['Soldered perfboard']=(box(pbd[0],pbd[1],zp-1.6,pbd[2],pbd[3],zp),(0.75,0.62,0.35),7)
parts['Floor plate (glued to the case floor)']=(FP['build_floor_plate'](),PLA,8)
# Peli 1400 base shell (approximate: straight walls, rounded corners), open at the front
IW,IH,RR,W=306.5,232.9,21.0,3.0
def rr(w,h,r,cx,cy): return F['rrect'](w,h,r,cx,cy)
z0=-F['RIM_DROP']
shell=Manifold.extrude(rr(IW+2*W,IH+2*W,RR+W,PW/2,PH/2),F['BASE_DEPTH']+W).translate([0,0,z0])-Manifold.extrude(rr(IW,IH,RR,PW/2,PH/2),F['BASE_DEPTH']).translate([0,0,z0-0.01])
parts['Peli 1400 base']=(shell,CASE,9)

def mesh(m): return m if isinstance(m,trimesh.Trimesh) else tm(m)
cache={k:(mesh(m),c,g) for k,(m,c,g) in parts.items()}

NOLABEL={'PMS7003 + adapter board'}
def labels_column(ax,img,proj,anchors,top=True,fs=9.5):
    """place labels in a row along the top (or bottom) edge, sorted by anchor x, with leader lines"""
    pts=[(k,proj(np.array(p))[0]) for k,p in anchors if k not in NOLABEL]
    pts.sort(key=lambda t:t[1][0]); n=len(pts); W=img.shape[1]
    for i,(k,q) in enumerate(pts):
        tx=W*(0.04+0.92*i/max(n-1,1)); ty=(25+ (i%2)*38) if top else img.shape[0]-25-(i%2)*38
        ax.annotate(k,xy=q,xytext=(tx,ty),ha='center',va='center',fontsize=fs,arrowprops=dict(arrowstyle='-',lw=0.7,color='#555'),bbox=dict(fc='white',ec='#c9cdd2',lw=0.6,pad=2.2))
        ax.plot([q[0]],[q[1]],'o',ms=3,color='#c1121f')
# ---- view 1: assembled, everything cut through at mid-height and seen from above and behind ----
YC=150.0
keep=box(-60,-60,-60,PW+60,YC,200)
items=[];anch=[]
for k,(m,c,g) in parts.items():
    mm=(m if not isinstance(m,trimesh.Trimesh) else m)^keep
    if mm.is_empty(): continue
    t=tm(mm); items.append((t,c)); b=t.bounds
    anch.append((k,[(b[0][0]+b[1][0])/2,b[1][1],(b[0][2]+b[1][2])/2]))
view1=(0.3,1.0,0.3)
EXP={0:-230,1:0,2:45,3:0,4:85,5:120,6:215,7:310,8:350,9:480}
LIFT={0:0,1:0,2:15,3:0,4:30,5:45,6:70,7:95,8:105,9:140}
items2=[];anch2=[]
for k,(m,c,g) in cache.items():
    t=m.copy(); t.apply_translation([0,LIFT[g],EXP[g]]); items2.append((t,c)); b=t.bounds
    anch2.append((k,[(b[0][0]+b[1][0])/2,b[1][1],(b[0][2]+b[1][2])/2]))
view2=(-0.95,0.5,-0.7)

fig=plt.figure(figsize=(18,25),dpi=100)
t0=time.time(); img,proj=render(items,view=view1,up=(0,1,0),W=1700,H=1150,margin=110); print('view1 %.0fs'%(time.time()-t0))
ax=fig.add_axes([0.02,0.535,0.96,0.40]); ax.imshow(img); ax.set_axis_off()
ax.set_title('Assembled: everything cut through at %.0f mm up and seen from above (panel at the top of the picture, case floor at the bottom)'%YC,fontsize=14,loc='left',color='#1d2124')
labels_column(ax,img,proj,anch,top=True)
t0=time.time(); img2,proj2=render(items2,view=view2,up=(0,1,0),W=1700,H=1250,margin=110); print('view2 %.0fs'%(time.time()-t0))
ax=fig.add_axes([0.02,0.07,0.96,0.44]); ax.imshow(img2); ax.set_axis_off()
ax.set_title('Exploded, front to back in assembly order (panel at the front left, case at the back right)',fontsize=14,loc='left',color='#1d2124')
labels_column(ax,img2,proj2,anch2,top=True)
steps=("ORDER  1 Inserts into every printed part · 2 Floor plate: inserts, then glue it to the case floor (Primer 94 / 770) · 3 Pi in its pocket, breakout and perfboard on the bosses\n"
       "       4 On the panel's back: pods, port tray + controls, PMS7003 cradle, screen + clamps · 5 Spacer + KVM onto the screen back (VHB), plug in the console side\n"
       "       6 Posts onto the panel (M3 × 10), VHB on their feet · 7 Connect everything, coil the spare KVM cable over the perfboard · 8 Lower the panel into the case: posts land on the floor")
fig.text(0.02,0.02,steps,fontsize=11,family='monospace',color='#1d2124',linespacing=1.6)
fig.text(0.02,0.985,'FIELDSTATION — base assembly in the Peli 1400',fontsize=20,fontweight='bold',color='#1d2124',va='top')
fig.text(0.02,0.968,'Parts from the CAD model; the Pi, KVM, boards and screen are shown as their measured outlines. The case shell is approximate.',fontsize=11,color='#555',va='top')
plt.savefig('../docs/case_assembly.png',facecolor='white'); print('saved')
