"""Where every part goes: base panel (front view), port pocket detail, lid (top view). All to scale from the models."""
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle, Circle, FancyBboxPatch
F={'__name__':'lib'}; exec(open('frame.py').read(),F)
L={'__name__':'lib'}; exec(open('lid.py').read(),L)
INK='#1d2124'; PANEL='#cfd3d6'; PART='#3a3f45'; ACC='#b9770e'; BLUE='#2f6e8f'; BEHIND='#2f6e8f'
def poly_patch(ax,cs,**k):
    v=[];c=[]
    for pl in cs.to_polygons():
        pl=np.asarray(pl); v+=list(pl)+[pl[0]]; c+=[Path.MOVETO]+[Path.LINETO]*(len(pl)-1)+[Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(v,c),**k))
def tag(ax,x,y,n,col=ACC):
    ax.add_patch(Circle((x,y),5.2,fc=col,ec='white',lw=1.2,zorder=20)); ax.text(x,y,str(n),ha='center',va='center',color='white',fontsize=8.5,fontweight='bold',zorder=21)
def dash(ax,x0,y0,w,h,col=BEHIND,lw=1.0):
    ax.add_patch(Rectangle((x0,y0),w,h,fill=False,ec=col,ls=(0,(4,2.5)),lw=lw,zorder=6))
fig=plt.figure(figsize=(17,22),dpi=110)
fig.text(0.03,0.985,'FIELDSTATION: where everything goes',fontsize=22,fontweight='bold',color=INK,va='top')
fig.text(0.03,0.968,'All drawings to scale from the print models. Base panel is seen from the front; dashed outlines are parts mounted behind it.',fontsize=11.5,color='#555',va='top')
# ---------------- base panel ----------------
ax=fig.add_axes([0.03,0.50,0.62,0.44]); PW,PH=F['PW'],F['PH']
poly_patch(ax,F['panel_2d'](),fc=PANEL,ec='#555',lw=0.7,zorder=1)
for x,y in F['clamp_holes']()+list(F['POSTS'].values())+F['TRAY_INS']+[(cx+dx,cy+dy) for cx,cy in F['PODS'] for dx in (-36,36) for dy in (-36,36)]+[(F['AIR_C'][0]+dx,F['AIR_C'][1]+dy) for dx,dy in [(-13,-12),(13,-12),(0,-32.2)]]:
    ax.add_patch(Circle((x,y),1.9,fc='white',ec='#555',lw=0.5,zorder=2))
# behind-panel parts
dash(ax,F['SC_X0'],F['SC_Y0'],F['SC_W'],F['SC_H'])                                 # screen case
for (x,y,sx,sy) in [(F['SC_X0'],F['SC_Y0'],1,1),(F['SC_X0']+F['SC_W'],F['SC_Y0'],-1,1),(F['SC_X0'],F['SC_Y0']+F['SC_H'],1,-1),(F['SC_X0']+F['SC_W'],F['SC_Y0']+F['SC_H'],-1,-1)]:
    ax.add_patch(Rectangle((min(x-sx*9,x+sx*24),min(y-sy*9,y)),33,9,fc='#7d8a95',alpha=0.55,ec='none',zorder=5))
    ax.add_patch(Rectangle((min(x-sx*9,x),min(y-sy*9,y+sy*24)),9,33,fc='#7d8a95',alpha=0.55,ec='none',zorder=5))
for cx,cy in F['PODS']: dash(ax,cx-40,cy-40,80,80)
dash(ax,F['PK_CX']-57.5,0.5,115,F['SC_Y0']-3.5)                                    # tray flange
dash(ax,F['AIR_C'][0]-17.5,F['AIR_C'][1]-37.2,35,63.4)                              # PMS cradle
for n,(x,y) in F['POSTS'].items(): ax.add_patch(Rectangle((x-5,y-5),10,10,fc='#7a5c3a',ec='none',zorder=7))
dash(ax,145,105,98.75,90.2,col='#888',lw=0.8); ax.text(145+49,105+8,'Pi 5 + UPS case (on case floor)',ha='center',fontsize=7.5,color='#666')
dash(ax,20,102,55,65,col='#888',lw=0.8); ax.text(47.5,105,'GPIO breakout',ha='center',fontsize=7.5,color='#666')
dash(ax,82,100,50,70,col='#888',lw=0.8); ax.text(107,103,'perfboard',ha='center',fontsize=7.5,color='#666')
# numbered tags
T=[(F['SC_CX'],F['SC_CY']+20,1),(F['SC_X0']+4,F['SC_Y0']+4,2),(F['PODS'][0][0],F['PODS'][0][1],3),(F['PODS'][1][0],F['PODS'][1][1],3),
   (F['PK_CX'],F['PK_CY'],4),(F['AIR_C'][0],F['AIR_C'][1]+10,5),(F['POSTS']['TL'][0],F['POSTS']['TL'][1]+12,6),(F['POSTS']['MR'][0],F['POSTS']['MR'][1]+12,6),
   (F['TEMP_C'][0],F['TEMP_C'][1]+46,7),(PW/2,PH-6,8)]
for x,y,n in T: tag(ax,x,y,n)
ax.plot([PW/2]*2,[0,PH],':',color='#c0392b',lw=0.9,zorder=8)
ax.set_xlim(-8,PW+8); ax.set_ylim(-8,PH+8); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('Base panel (front view)  ·  302.5 × 228.8 mm, sits 8 mm below the rim',fontsize=13,loc='left',color=INK)
# ---------------- legend for base ----------------
lg=fig.add_axes([0.66,0.50,0.32,0.44]); lg.axis('off')
rows=[(1,'Screen in its case','Behind the 156 × 88 mm window, held by the corner clamps','—'),
      (2,'Screen clamps ×4','One on each case corner. 2 × M3 × 8 each, from the front','B3'),
      (3,'Speaker pods ×2','Grille centres 52 mm in from each side, 48 mm up. 4 × M3 × 20 each','pods plate'),
      (4,'Port tray','Recessed pocket between the pods. 4 × M3 × 8. Detail below','B3 / B3a'),
      (5,'PMS7003 cradle','Behind the AIR louvres, snout to the panel. 3 × M3 × 8','B3 / B3a'),
      (6,'Floor posts ×4','2 top corners, 2 beside the pods. M3 × 10 from the front; VHB feet','B3'),
      (7,'TEMP column','Vent slots; KVM remote button holder goes here','B2 (pending)'),
      (8,'Panel seam','Halves epoxied at the dovetails; splice strip behind, above the window','B1 + B2')]
y=0.97
lg.text(0.0,y,'#',fontsize=10,fontweight='bold',color='#666'); lg.text(0.08,y,'Part',fontsize=10,fontweight='bold',color='#666'); lg.text(0.80,y,'Plate',fontsize=10,fontweight='bold',color='#666')
for n,name,desc,pl in rows:
    y-=0.105
    lg.add_patch(Circle((0.025,y+0.008),0.022,transform=lg.transAxes,fc=ACC,ec='none')); lg.text(0.025,y+0.008,str(n),transform=lg.transAxes,ha='center',va='center',color='white',fontsize=9,fontweight='bold')
    lg.text(0.08,y+0.02,name,fontsize=11,fontweight='bold',color=INK,transform=lg.transAxes); lg.text(0.08,y-0.025,desc,fontsize=9,color='#444',transform=lg.transAxes,wrap=True)
    lg.text(0.80,y+0.02,pl,fontsize=10,color=BLUE,transform=lg.transAxes)
lg.text(0.0,0.02,'Dashed blue: mounted behind the panel. Brown squares: posts.\nGrey dashed: parts on the case floor (not attached to the panel).',fontsize=8.8,color='#555',transform=lg.transAxes)
# ---------------- port pocket detail ----------------
ax=fig.add_axes([0.03,0.25,0.50,0.23]); cx,cy,W,H=F['PK_CX'],F['PK_CY'],F['PK_W'],F['PK_H']
ax.add_patch(Rectangle((cx-W/2,cy-H/2),W,H,fc='#e9ebe8',ec=INK,lw=1.3))
labels=[]
for i,((x,y),t) in enumerate(zip(F['USB'],['USB-A  (to Pi USB 3)','USB-A  (to Pi USB 3)','USB-C  (KVM laptop input)'])):
    ax.add_patch(Rectangle((x-13,y-15.5),26,31,fc=PART,ec='none')); ax.add_patch(Circle((x,y),12.1,fc='#6b7178',ec='none'))
    for dx,dy in [(-9.5,12),(9.5,-12)]: ax.add_patch(Circle((x+dx,y+dy),1.65,fc='white',ec='none'))
    ax.text(x,y,['A','A','C'][i],ha='center',va='center',color='white',fontsize=11,fontweight='bold')
    labels.append((x,y+15.5,t,'up'))
for (p,d,t) in [(F['BTN'],12.3,'Power (X1202 button)  ⌀12.3'),(F['DCJ'],11.2,'DC 12 V in  ⌀11.2'),(F['TOG'],12.2,'Audio on/off  ⌀12.2'),(F['POT'],7.2,'Volume pot  ⌀7.2')]:
    ax.add_patch(Circle(p,d/2,fc='white',ec=INK,lw=1.1))
    if 'Volume' in t: ax.add_patch(Circle(p,10.2,fill=False,ec='#888',ls='--',lw=0.9))
    labels.append((p[0],p[1],t,'side'))
x,y=F['KB_PASS']; w,h=F['KB_PASS_W'],F['KB_PASS_H']
ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle=f"round,pad=0,rounding_size={h/2-0.01}",fc='white',ec=ACC,lw=1.6,zorder=3))
ax.annotate('Keyboard cable slot 24 × 12\n(lines up with the lid slot)',xy=(x+w/2,y),xytext=(cx+W/2+4,cy-H/2-14),fontsize=9,color='#8a5a0a',
            arrowprops=dict(arrowstyle='-',color='#8a5a0a',lw=0.8),ha='left',va='center')
ups=[l for l in labels if l[3]=='up']
for (px,py,t,mode),dy in zip(ups,[8,19,8]):
    ax.annotate(t,xy=(px,py),xytext=(px,py+dy),fontsize=8.6,ha='center',arrowprops=dict(arrowstyle='-',lw=0.6,color='#555'))
sides=[l for l in labels if l[3]=='side']
for (px,py,t,mode),(tx,ty) in zip(sides,[(cx-W/2-4,cy-H/2-10),(cx-W/2-4,cy-H/2-20),(cx-W/2-4,cy-H/2-30),(cx+W/2+4,cy-H/2-28)]):
    ax.annotate(t,xy=(px,py),xytext=(tx,ty),fontsize=8.6,ha='right' if tx<cx else 'left',va='center',arrowprops=dict(arrowstyle='-',lw=0.6,color='#555'))
ax.set_xlim(cx-W/2-62,cx+W/2+62); ax.set_ylim(cy-H/2-36,cy+H/2+30); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('Port pocket (front view, 106 × 76 mm, floor 18 mm deep)',fontsize=13,loc='left',color=INK)
pk=fig.add_axes([0.56,0.25,0.42,0.23]); pk.axis('off')
txt=("Fitting the port tray\n\n"
     "• USB sockets: from the front, 2 × M3 × 10 bolt + nut each\n"
     "  (diagonal corners). Socket body goes behind the tray floor.\n"
     "• Power, DC jack, audio: through from the front,\n"
     "  own nut tightened on the back.\n"
     "• Volume pot: from the back, nut on the front, then the knob.\n"
     "  Snip its anti-rotation tab if it has one.\n"
     "• Keyboard cable: plug it into a front USB-A when in use;\n"
     "  feed it back through the bottom slot when packing.\n"
     "• Tray to panel: 4 × M3 × 8 countersunk from the front\n"
     "  into the tray's flange inserts.")
pk.text(0,0.98,txt,fontsize=10.5,va='top',color=INK,linespacing=1.45)
# ---------------- lid ----------------
ax=fig.add_axes([0.03,0.02,0.55,0.22]); LPW,LPH=L['PW'],L['PH']
ax.add_patch(Rectangle((L['KX0'],L['KY0']),L['KB_W'],L['KB_D'],fc='#c3c7cc',ec='#888',lw=0.6,zorder=0))
ov=L['rrect'](LPW,LPH,L['PR'],LPW/2,LPH/2)-L['rrect'](L['KB_W']-9,L['KB_D']-8,3,LPW/2,(L['KY0']+5+L['KY1']-3)/2)-L['rrect'](L['PASS_W'],L['PASS_H'],L['PASS_H']/2-0.01,L['CABLE_X'],L['PASS_Y'])\
   -L['rrect'](L['DOOR_X1']-L['DOOR_X0'],L['DOOR_Y1']-L['DOOR_Y0'],L['DOOR_R'],(L['DOOR_X0']+L['DOOR_X1'])/2,(L['DOOR_Y0']+L['DOOR_Y1'])/2)-L['circ'](18,L['NOTCH'][0],L['NOTCH'][1]-1)
poly_patch(ax,ov,fc=PANEL,ec='#555',lw=0.7,zorder=2)
ax.add_patch(Rectangle((L['DOOR_X0']+0.3,L['DOOR_Y0']+0.3),L['DOOR_X1']-L['DOOR_X0']-0.6,L['DOOR_Y1']-L['DOOR_Y0']-0.6,fc='#b6bbc0',ec='#555',lw=0.7,zorder=3))
for x,y in L['insert_points'](): ax.add_patch(Circle((x,y),1.9,fc='white',ec='#555',lw=0.5,zorder=4))
dash(ax,L['CX0'],L['CY0'],L['CX1']-L['CX0'],L['CY1']-L['CY0'])
for x,y,n in [(LPW/2,(L['KY0']+L['KY1'])/2,'A'),(L['CABLE_X'],L['PASS_Y']+12,'B'),((L['DOOR_X0']+L['DOOR_X1'])/2,(L['DOOR_Y0']+L['DOOR_Y1'])/2,'C'),(L['CX0']+10,L['CY0']+10,'D')]: tag(ax,x,y,n,col=BLUE)
ax.text(LPW/2,LPH+6,'hinge',ha='center',fontsize=9,color='#666'); ax.text(LPW/2,-9,'front edge (you sit here)',ha='center',fontsize=9,color='#666')
ax.set_xlim(-8,LPW+8); ax.set_ylim(-14,LPH+12); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('Lid (top view, open)',fontsize=13,loc='left',color=INK)
ll=fig.add_axes([0.60,0.02,0.38,0.22]); ll.axis('off')
ll.text(0,0.98,("A  Keyboard: sits in the cradle, trackball edge toward the hinge.\n"
                "    Overlay laps its aluminium border. 12 × M3 × 8 into the cradle (K1–K4).\n\n"
                "B  Keyboard cable slot: cable runs up over the hinge to the\n"
                "    pocket's bottom slot (same left-right position).\n\n"
                "C  Accessory tray door: lift-off, 4 magnet cubes (K4 + K2).\n\n"
                "D  Cradle outline (dashed): VHB or Dual Lock to the lid floor.\n"
                "    About 6 mm gap to the walls is intentional; the overlay covers it."),
        fontsize=10.5,va='top',color=INK,linespacing=1.45)
plt.savefig('../docs/placement_sheet.png',facecolor='white')
print('saved')
