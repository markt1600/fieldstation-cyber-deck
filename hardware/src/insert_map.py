"""Draws ../docs/insert_map.png: where the heat-set inserts go in the v2 base frame (floor plate, post feet, pod brackets)."""
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.path import Path; from matplotlib.patches import PathPatch, Rectangle, Circle
g={'__name__':'lib'}; exec(open('floorplate.py').read().split("if __name__")[0],g)
F=g; PW=g['PW']; POSTS=g['POSTS']
fig=plt.figure(figsize=(18,12))
ax=fig.add_axes([0.03,0.36,0.62,0.56])
m=g['build_floor_plate'](); FZ=g['FLOOR_Z']
for z,c in [(FZ-1.5,'#ced4da'),(FZ-4,'#6c757d')]:
    v=[];cd=[]
    for p in m.slice(z).to_polygons():
        p=np.asarray(p); v+=list(map(tuple,p))+[tuple(p[0])]; cd+=[Path.MOVETO]+[Path.LINETO]*(len(p)-1)+[Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(v,cd),fc=c,ec='k',lw=0.5))
x0,y0,x1,y1,t=g['SPLICE']; ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fc='#ffb703',alpha=0.6,ec='k',label='splice strip (glue on top)'))
ax.plot([g['SEAM_X']]*2,[g['FP'][1],g['FP'][3]],'k--',lw=0.8)
csk=[h for n in POSTS for h in g['foot_holes'](n)]+[h for k in g['POD_BRK'] for h in g['brk_holes'](k)]
ax.scatter(*zip(*csk),s=60,marker='x',c='#c1121f',zorder=5,label='screw hole, M3 × 8 csk from underneath (no insert)')
ax.scatter(*zip(*g['bo_holes']()),s=90,facecolors='none',edgecolors='#2a9d8f',linewidths=2.5,zorder=5,label='M3 insert (GPIO breakout bosses) ×2')
ax.scatter(*zip(*g['pb_holes']()),s=70,facecolors='none',edgecolors='#7b2cbf',linewidths=2.5,zorder=5,label='M2 insert (perfboard bosses) ×4')
ax.set_xlim(10,292); ax.set_ylim(80,218); ax.set_aspect('equal'); ax.legend(loc='upper center',bbox_to_anchor=(0.5,-0.06),ncol=2,fontsize=10)
ax.set_title('Floor plate, top side (seen from the front of the case)',fontsize=13)
# feet: underside views
def foot_panel(rect,holes,title,pos,top=None):
    a=fig.add_axes(pos); fx0,fy0,fx1,fy1=rect
    a.add_patch(Rectangle((fx0,fy0),fx1-fx0,fy1-fy0,fc='#adb5bd',ec='k'))
    if top: a.add_patch(Rectangle(top[:2],top[2],top[3],fc='#6c757d',ec='k')); a.text(top[0]+top[2]/2,top[1]+top[3]/2,'column',ha='center',va='center',fontsize=8,color='w')
    for hx,hy in holes: a.add_patch(Circle((hx,hy),2.0,fc='#e9c46a',ec='#9c6644',lw=2))
    a.set_xlim(fx0-6,fx1+6); a.set_ylim(fy0-6,fy1+6); a.set_aspect('equal'); a.set_xticks([]); a.set_yticks([]); a.set_title(title,fontsize=10)
i=0
for n in ('TL','TR','ML','MR'):
    x,y=POSTS[n]; sx=1 if x<PW/2 else -1
    fx0,fx1=(x-5,x+21) if sx>0 else (x-21,x+5); fy0,fy1=(y-13,y+5) if n in ('TL','TR') else (y-5,y+5)
    foot_panel((fx0,fy0,fx1,fy1),g['foot_holes'](n),'post %s foot\n2 × M3 insert in the underside'%n,[0.68+(i%2)*0.155,0.66-(i//2)*0.20,0.14,0.17],top=(x-5,y-5,10,10)); i+=1
for j,k in enumerate(('L','R')):
    bx0,bx1=g['POD_BRK'][k]
    foot_panel((bx0,g['BRK_Y0'],bx1,g['BRK_Y1']),g['brk_holes'](k),'%s pod bracket foot\n2 × M3 insert in the underside'%('left' if k=='L' else 'right'),[0.68+j*0.155,0.26,0.14,0.17])
fig.text(0.68,0.20,'Each post also keeps its 1 × M3 insert in the top\n(panel end), for the M3 × 10 screw through the panel.\n\nTotals for the frame: M3 inserts 2 (breakout) + 8 (post feet)\n+ 4 (bracket feet) + 4 (post tops) = 18;  M2 inserts 4 (perfboard).\nFeet are drawn in the same orientation as the plate (seen\nfrom the front of the case); the insert holes are in the\nunderside, facing the floor plate.',fontsize=10.5,va='top')
fig.text(0.03,0.975,'Heat-set inserts in the base frame (v2)',fontsize=20,weight='bold',va='top')
fig.text(0.03,0.945,'The floor plate itself has no inserts for the frame: the 12 screws pass up through its countersunk holes (red ×) into inserts in the post and bracket feet.',fontsize=11,color='#444',va='top')
fig.savefig('../docs/insert_map.png',dpi=90); print('wrote ../docs/insert_map.png')
