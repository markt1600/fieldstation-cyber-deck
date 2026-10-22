"""Draws ../docs/pms7003_cradle.png: sections through the PMS7003 cradle with the sensor, adapter board and plugs."""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from manifold3d import Manifold
S={'__name__':'lib'}; exec(open('pms7003_v2.py').read().split("o=body.to_mesh()")[0],S)
box=S['box']; SN=S['SNOUT']
sensor,brd,conn,plugs=S['board_parts']()
panel=box(-40,-50,-4,40,45,0)
for k in range(-5,6):                                   # louvres in front of the cradle (as frame.py)
    if k==0: continue
    panel=panel-box(-5,k*4.2-1.0,-5,5,k*4.2+1.0,1)
parts=[('panel',panel,'#9aa3ad'),('cradle',S['body'],'#f2a23a'),('sensor',sensor,'#3a9fbf'),
       ('connector',conn,'#333333'),('adapter board',brd,'#2e9e4f'),('Dupont plugs + pins',plugs,'#222222')]

def draw(ax,axis,at,title):
    for name,m,c in parts:
        if axis=='y': polys=m.rotate([90,0,0]).slice(at).to_polygons(); f=lambda p:(p[:,1]*-1,p[:,0])
        else:         polys=m.rotate([0,90,0]).slice(-at).to_polygons(); f=lambda p:(p[:,0],p[:,1])
        if not polys: continue
        verts=[];codes=[]
        for p in polys:
            p=np.asarray(p); u,v=f(p)
            verts+=list(zip(u,v))+[(u[0],v[0])]; codes+=[Path.MOVETO]+[Path.LINETO]*(len(p)-1)+[Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts,codes),fc=c,ec='k',lw=0.6,label=name))
    ax.set_aspect('equal'); ax.autoscale_view(); ax.set_title(title,fontsize=10); ax.grid(alpha=0.2)
    ax.set_xlabel('depth behind the back of the panel (mm)')

fig,axs=plt.subplots(1,2,figsize=(15,7.5))
draw(axs[0],'y',18.0,'Section through the plugs and the adapter board (y = +18)\npanel on the left, case interior to the right')
axs[0].set_ylabel('across the sensor (x, mm); board side up')
draw(axs[1],'x',0.0,'Section down the middle of the duct (x = 0)\ninlet + plugs chamber (top) and outlet chamber (bottom), split by the rib')
axs[1].set_ylabel('along the sensor (y, mm); board end up')
h,l=axs[0].get_legend_handles_labels(); axs[0].legend(h,l,loc='lower right',fontsize=8)
for ax in axs: ax.set_xlim(-8,80); ax.set_ylim(-50,48)
axs[0].annotate('pin notch: pack\nwith foam',xy=(SN-4,7),xytext=(SN-28,24),arrowprops=dict(arrowstyle='->'),fontsize=8)
axs[0].annotate('sleeve open on the board side\nso the connector slides past',xy=(SN+8,8),xytext=(SN+12,24),arrowprops=dict(arrowstyle='->'),fontsize=8)
axs[0].annotate('plugs sit mid-thickness\nin the inlet chamber',xy=(SN-12,0),xytext=(SN-36,-24),arrowprops=dict(arrowstyle='->'),fontsize=8)
axs[1].annotate('wires leave through the\nend-wall slot (seal with foam)',xy=(8,25),xytext=(4,38),arrowprops=dict(arrowstyle='->'),fontsize=8)
axs[1].annotate('sensor drops in from the back,\nface first; cable tie over its back',xy=(SN+30,10),xytext=(SN+8,-44),arrowprops=dict(arrowstyle='->'),fontsize=8)
fig.suptitle('PMS7003 cradle: the sensor face sits %.0f mm behind the panel, sealed to the louvres by the duct (foam on the lip)\nSensor in the right-hand column, adapter board facing the screen'%SN,fontsize=11)
fig.tight_layout(); fig.savefig('../docs/pms7003_cradle.png',dpi=130)
print('wrote ../docs/pms7003_cradle.png')
