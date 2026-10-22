"""Draws ../docs/internal_layout.png: everything behind the base panel, in three views, with the proposed KVM spot."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
src=open('check.py').read(); exec(src.split("names=list(parts)")[0])

def bb(m):
    b=to_tm(m).bounds; return [*b[0],*b[1]]
items=[]   # (label, [x0,y0,z0,x1,y1,z1], colour, hatch)
items.append(('screen (7" in case)',bb(parts['screen']),'#5b8def',None))
for i,k in enumerate(['pod0','pod1']): items.append(('speaker pod' if i==0 else None,bb(parts[k]),'#c77dff',None))
items.append(('port tray',bb(parts['tray']),'#9aa3ad',None))
items.append(('PMS7003 + cradle',bb(parts['air']),'#f2a23a',None))
for n in POSTS: items.append(('floor posts' if n=='TL' else None,bb(parts['post'+n]),'#6c757d',None))
items.append(('Pi 5 in X1202 case',bb(parts['pi']),'#2a9d8f',None))
items.append(('GPIO breakout',bb(parts['breakout']),'#80b918',None))
items.append(('mini breadboard',bb(parts['breadboard']),'#e9c46a',None))
cl=[(SC_X0,SC_Y0,1,1),(SC_X0+SC_W,SC_Y0,-1,1),(SC_X0,SC_Y0+SC_H,1,-1),(SC_X0+SC_W,SC_Y0+SC_H,-1,-1)]
for i,(cx,cy,sx,sy) in enumerate(cl):
    x0,x1=sorted([cx-sx*9,cx+sx*24]); y0,y1=sorted([cy-sy*9,cy+sy*24])
    items.append(('screen clamps' if i==0 else None,[x0,y0,T,x1,y1,T+19.7],'#adb5bd',None))
KVM=[42,114,25,139,205,48]
items.append(('KVM (C2-H46) — proposed',KVM,'#e63946',None))
items.append(('right-angle HDMI/USB-A plugs',[60,205,25,121,223,48],'#e63946','///'))
items.append(('host-cable bend + coil',[55,89,25,126,114,48],'#ffb3b8','..'))

LAYERS=[('Layer 1: on the panel (z 4–24)',4,24),('Layer 2: just behind the screen (z 24–50)',24,50),('Layer 3: on the case floor (z 50–91)',50,91)]
fig=plt.figure(figsize=(17,14))
gs=fig.add_gridspec(2,2)
def frame(ax,title):
    ax.add_patch(Rectangle((0,0),PW,PH,fc='#f8f9fa',ec='k',lw=1.2))
    ax.add_patch(Rectangle((PK_CX-PK_W/2,PK_CY-PK_H/2),PK_W,PK_H,fc='none',ec='k',ls='--',lw=0.8))
    ax.set_xlim(-4,PW+4); ax.set_ylim(-4,PH+4); ax.set_aspect('equal'); ax.set_title(title,fontsize=11); ax.grid(alpha=0.15)
    ax.set_xlabel('x (mm), seen from the front'); ax.set_ylabel('y (mm, up)')
for i,(title,z0,z1) in enumerate(LAYERS):
    ax=fig.add_subplot(gs[i//2,i%2]); frame(ax,title)
    for lab,bx,c,h in items:
        if bx[5]<=z0+0.5 or bx[2]>=z1-0.5: continue
        ax.add_patch(Rectangle((bx[0],bx[1]),bx[3]-bx[0],bx[4]-bx[1],fc=c if h is None else 'none',ec=c if h else 'k',hatch=h,alpha=0.6 if h is None else 0.9,lw=0.8,label=lab))
        if lab and h is None and 'clamps' not in lab and 'posts' not in lab:
            ax.text((bx[0]+bx[3])/2,(bx[1]+bx[4])/2,'%s\nz %.0f–%.0f'%(lab,bx[2],bx[5]),ha='center',va='center',fontsize=8)
        elif lab and h:
            ax.text((bx[0]+bx[3])/2,(bx[1]+bx[4])/2,lab,ha='center',va='center',fontsize=7,color='#9d0208')
    if i==0: ax.text(PK_CX,PK_CY-PK_H/2+4,'port pocket (USB-C socket = PC2 in)',ha='center',fontsize=7)
    if i==1:
        ax.annotate('PC2 USB-C → back of the\npocket USB-C socket',xy=(PK_CX,PK_CY+18.5),xytext=(150,40),fontsize=8,arrowprops=dict(arrowstyle='->',color='r'))
        ax.annotate('PC1 HDMI + USB-A → Pi\n(micro-HDMI adapter)',xy=(160,150),xytext=(160,70),fontsize=8,arrowprops=dict(arrowstyle='->',color='r'))
        ax.annotate('console edge: HDMI → screen,\nUSB-A → keyboard cable',xy=(90,214),xytext=(150,218),fontsize=8,arrowprops=dict(arrowstyle='->',color='r'))
# side view
ax=fig.add_subplot(gs[1,1])
ax.add_patch(Rectangle((0,0),FLOOR_Z,PH,fc='#f8f9fa',ec='k',lw=1.2)); ax.axvspan(0,T,color='#ced4da')
for lab,bx,c,h in sorted(items,key=lambda it:it[1][0]):
    ax.add_patch(Rectangle((bx[2],bx[1]),bx[5]-bx[2],bx[4]-bx[1],fc=c if h is None else 'none',ec=c if h else 'k',hatch=h,alpha=0.45 if h is None else 0.9,lw=0.8,label=lab))
for z,l in [(z0,'') for _,z0,_ in LAYERS[1:]]: ax.axvline(z,color='k',ls=':',lw=0.8)
ax.text(2,PH+6,'panel',fontsize=8); ax.text(FLOOR_Z-14,PH+6,'case floor',fontsize=8)
ax.set_xlim(-4,FLOOR_Z+4); ax.set_ylim(-4,PH+12); ax.set_aspect('equal')
ax.set_title('Side view (from the right; panel on the left; dotted lines = layer boundaries)',fontsize=11)
ax.set_xlabel('depth behind the panel front, z (mm)'); ax.set_ylabel('y (mm, up)')
h,l=ax.get_legend_handles_labels(); d=dict(zip(l,h)); d.pop(None,None); d={k:v for k,v in d.items() if k and k!='_nolegend_'}
ax.legend(d.values(),d.keys(),loc='center left',bbox_to_anchor=(1.02,0.5),fontsize=9,title='Behind the base panel')
fig.suptitle('FieldStation base: what sits where behind the panel, with the proposed KVM spot\n(bounding boxes; the clash check uses the real shapes. Remote button position still to be decided.)',fontsize=13)
fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig('../docs/internal_layout.png',dpi=100)
print('wrote ../docs/internal_layout.png')
