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
items.append(('floor plate',bb(parts['floor_plate']),'#ced4da',None))
items.append(('Pi 5 in X1202 case',bb(parts['pi']),'#2a9d8f',None))
items.append(('GPIO breakout',bb(parts['breakout']),'#80b918',None))
items.append(('soldered perfboard (70 × 50)',bb(parts['breadboard']),'#e9c46a',None))
cl=[(SC_X0,SC_Y0,1,1),(SC_X0+SC_W,SC_Y0,-1,1),(SC_X0,SC_Y0+SC_H,1,-1),(SC_X0+SC_W,SC_Y0+SC_H,-1,-1)]
for i,(cx,cy,sx,sy) in enumerate(cl):
    x0,x1=sorted([cx-sx*9,cx+sx*24]); y0,y1=sorted([cy-sy*9,cy+sy*24])
    items.append(('screen clamps' if i==0 else None,[x0,y0,T,x1,y1,T+19.7],'#adb5bd',None))
items.append(('screen HDMI + micro-USB plugs',[SC_X0-42,SC_Y0+26,T+1,SC_X0,SC_Y0+69,T+SC_T],'#1d3557','xx'))
items.append(('screen cables turning up/back',[SC_X0-48,SC_Y0+26,T+SC_T,SC_X0-14,SC_Y0+97,T+44],'#457b9d','..'))
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
# section through the stack at x = XS (screen, KVM, breakout, perfboard, floor plate)
XS=92.0
for a in fig.axes[:3]: a.axvline(XS,color='k',ls='-.',lw=0.8); a.text(XS+1,2,'section',fontsize=7)
ax=fig.add_subplot(gs[1,1])
ax.add_patch(Rectangle((0,0),FLOOR_Z,PH,fc='#f8f9fa',ec='k',lw=1.2)); ax.axvspan(0,T,color='#ced4da')
ax.text(0.5,PH+3,'panel',fontsize=8); ax.text(FLOOR_Z-16,PH+3,'case floor',fontsize=8)
for lab,bx,c,h in items:
    if not (bx[0]<=XS<=bx[3]): continue
    if lab=='floor plate': bx=bx[:2]+[FLOOR_Z-3]+bx[3:]
    ax.add_patch(Rectangle((bx[2],bx[1]),bx[5]-bx[2],bx[4]-bx[1],fc=c if h is None else 'none',ec=c if h else 'k',hatch=h,alpha=0.6 if h is None else 0.9,lw=0.8,label=lab))
def gap(z0,z1,y,txt):
    ax.annotate('',xy=(z0,y),xytext=(z1,y),arrowprops=dict(arrowstyle='<->',lw=0.8)); ax.text((z0+z1)/2,y+2,txt,ha='center',fontsize=7)
gap(T+SC_T,25,175,'4'); gap(48,50,185,'2'); gap(48,FLOOR_Z-9-1.6-15,120,'17')
ax.text(12,160,'screen',rotation=90,fontsize=8,va='center'); ax.text(36,160,'KVM',rotation=90,fontsize=8,va='center')
ax.text(67,170,'breakout\n(35 mm space)',fontsize=7,ha='center',va='center'); ax.text(74,115,'perfboard\nwire space',fontsize=7,ha='center',va='center')
ax.text(40,50,'speaker pod',fontsize=8,ha='center'); ax.text(84,140,'floor plate',rotation=90,fontsize=7,va='center')
ax.set_xlim(-4,FLOOR_Z+4); ax.set_ylim(-4,PH+8); ax.set_aspect('equal')
ax.set_title('Section at x = %.0f mm, seen from the right (panel on the left)\nnumbers = gaps in mm'%XS,fontsize=11)
ax.set_xlabel('depth behind the panel front, z (mm)'); ax.set_ylabel('y (mm, up)')
h,l=[],[]
for a in fig.axes:
    hh,ll=a.get_legend_handles_labels(); h+=hh; l+=ll
d={}
for hh,ll in zip(h,l):
    if ll and not ll.startswith('_') and ll not in d: d[ll]=hh
ax.legend(d.values(),d.keys(),loc='center left',bbox_to_anchor=(1.02,0.5),fontsize=9,title='Behind the base panel')
fig.suptitle('FieldStation base: everything behind the panel, layer by layer\n(bounding boxes; the clash check uses the real shapes. Remote button lives in the lid’s magnetic tray.)',fontsize=13)
fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig('../docs/internal_layout.png',dpi=100)
print('wrote ../docs/internal_layout.png')
