import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, FancyBboxPatch, Circle, Rectangle
g={'__name__':'lib'}; exec(open('lid.py').read(),g)
PW,PH,KX0,KX1,KY0,KY1=g['PW'],g['PH'],g['KX0'],g['KX1'],g['KY0'],g['KY1']
rrect,rect,circ=g['rrect'],g['rect'],g['circ']
fig,ax=plt.subplots(figsize=(13,10.4),dpi=120)
INK='#22262a'; PANEL='#3a3f45'; PLATE='#c9cdd2'; KEY='#1b1c1e'; LEG='#e8eaec'
# lid case rim
ax.add_patch(FancyBboxPatch((-17.75+30,-16.6+30),338-60,262-60,boxstyle="round,pad=30",fc='#15171a',ec='none',zorder=0))
# keyboard plate (visible inside the opening)
ax.add_patch(FancyBboxPatch((KX0+3,KY0+3),286-6,149-6,boxstyle="round,pad=3",fc=PLATE,ec='#8d9298',lw=0.6,zorder=1))
# keys
pitch=(286-14)/15.0; gap=2.2
def keyrow(y,h,units,labels,x0=KX0+7):
    x=x0
    for u,l in zip(units,labels):
        w=u*pitch
        ax.add_patch(FancyBboxPatch((x+gap/2+1,y+1),w-gap-2,h-2,boxstyle="round,pad=1",fc=KEY,ec='none',zorder=2))
        if l: ax.text(x+w/2,y+h/2,l,ha='center',va='center',color=LEG,fontsize=6.2 if len(l)<4 else 5.2,zorder=3,fontfamily='DejaVu Sans')
        x+=w
y=KY0+8.68
# bottom row
keyrow(y,pitch,[1,1,1,1.25,5.5,1.25,1,1,1,1],['Ctrl','Fn','⊞','Alt','','Alt','Ctrl','◄','PgDn','►'])
# fix arrow cluster labels on last keys
y+=pitch
keyrow(y,pitch,[1.75,1,1,1,1,1,1,1,1,1,1,1.25,1,1],['Shift','Z','X','C','V','B','N','M',',','.','/','Shift','PgUp','End'])
y+=pitch
keyrow(y,pitch,[1.75,1,1,1,1,1,1,1,1,1,1,1,2.25],['Caps','A','S','D','F','G','H','J','K','L',';',"'",'Enter'])
y+=pitch
keyrow(y,pitch,[1.5,1,1,1,1,1,1,1,1,1,1,1,1,1.5],['Tab','Q','W','E','R','T','Y','U','I','O','P','[',']','\\'])
y+=pitch
keyrow(y,pitch,[1,1,1,1,1,1,1,1,1,1,1,1,1,2],['`','1','2','3','4','5','6','7','8','9','0','-','=','Bksp'])
y+=pitch
fh=pitch*0.62
keyrow(y,fh,[1]*13+[2],['Esc','F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12','Del'])
yb=y+fh
# back strip: scroll disc + wheel (left), LEDs, trackball (right)
ax.add_patch(Circle((KX0+20,KY1-13),9.5,fc='#2a2c2f',zorder=2)); ax.add_patch(Rectangle((KX0+36,KY1-19),5,13,angle=20,fc='#111',zorder=2))
for i in range(3): ax.add_patch(Rectangle((KX0+70+i*14,KY1-9),3,1.4,fc='#555',zorder=2))
ax.add_patch(Circle((KX1-22,KY1-15),12.5,fc='#2a2b2d',zorder=2)); ax.add_patch(Circle((KX1-22,KY1-15),9.0,fc='#0b0b0b',zorder=3))
ax.add_patch(Circle((KX1-24.5,KY1-12.5),2.2,fc='#3a3a3a',zorder=4))
# overlay with openings
p=g['build_overlay']()
poly=rrect(PW,PH,g['PR'],PW/2,PH/2)-rrect(286-9.0,149-8.0,3,PW/2,(KY0+5.0+KY1-3.0)/2)-rrect(g['PASS_W'],g['PASS_H'],g['PASS_H']/2-0.01,g['CABLE_X'],g['PASS_Y'])\
     -rrect(g['DOOR_X1']-g['DOOR_X0'],g['DOOR_Y1']-g['DOOR_Y0'],g['DOOR_R'],(g['DOOR_X0']+g['DOOR_X1'])/2,(g['DOOR_Y0']+g['DOOR_Y1'])/2)-circ(18,g['NOTCH'][0],g['NOTCH'][1]-1.0)
v=[];c=[]
for pl in poly.to_polygons():
    pl=np.asarray(pl); v+=list(pl)+[pl[0]]; c+=[Path.MOVETO]+[Path.LINETO]*(len(pl)-1)+[Path.CLOSEPOLY]
ax.add_patch(PathPatch(Path(v,c),fc=PANEL,ec='#1e2124',lw=0.8,zorder=5))
for x,yy in g['insert_points'](): ax.add_patch(Circle((x,yy),3.45,fc='#2b2f33',ec='#555b61',lw=0.5,zorder=6)); ax.add_patch(Circle((x,yy),1.0,fc='#888',zorder=7))
# tray door (closed) + its magnets (hidden, dashed)
d0x,d1x,d0y,d1y=g['DOOR_X0']+0.3,g['DOOR_X1']-0.3,g['DOOR_Y0']+0.3,g['DOOR_Y1']-0.3
ax.add_patch(FancyBboxPatch((d0x+3.7,d0y+3.7),d1x-d0x-7.4,d1y-d0y-7.4,boxstyle="round,pad=3.7",fc='#41474d',ec='#1e2124',lw=0.8,zorder=6))
for mx,my in g['MAGS']: ax.add_patch(Circle((mx,my),3.1,fill=False,ec='#9aa1a8',ls=(0,(1.5,1.2)),lw=0.7,zorder=7))
ax.add_patch(Circle((g['NOTCH'][0],g['NOTCH'][1]-1.0),9,fc='#2b2e31',ec='none',zorder=5.5))
# cable slot: show the cable coming through
ax.add_patch(FancyBboxPatch((g['CABLE_X']-12+7,g['PASS_Y']-7+7),24-14,14-14,boxstyle="round,pad=7",fc='#0e0f10',ec='none',zorder=5.6))
ax.plot([g['CABLE_X'],g['CABLE_X']],[g['PASS_Y'],PH+18],color='#0a0a0a',lw=3.2,zorder=8,solid_capstyle='round')
ax.add_patch(Rectangle((g['CABLE_X']-8,PH+12),16,12,fc='#2b2b2b',zorder=8))
# labels
def lab(x,y,t,col='#1d2124',**k): ax.text(x,y,t,fontsize=8.5,color=col,ha='center',va='center',zorder=10,**k)
lab((d0x+d1x)/2,(d0y+d1y)/2+3,'ACCESSORY TRAY',col='#d8dcdf',fontweight='bold'); lab((d0x+d1x)/2,(d0y+d1y)/2-5,'magnetic lift-off door · 124 × 46 × 25 mm inside',col='#b8bec4')
lab(g['CABLE_X'],g['PASS_Y']-12.5,'keyboard cable → port pocket',col='#d8dcdf')
lab(PW/2,PH+30,'HINGE  (base panel stands here when open)',col='#55595e')
lab(PW/2,-22,'front edge (you sit here)',col='#55595e')
lab(KX0+20,KY1-29,'scroll',col='#33373b'); lab(KX1-22,KY1-33,'trackball',col='#33373b')
# dimensions
def dim(x0,y0,x1,y1,t,off=(0,0)):
    ax.annotate('',xy=(x0,y0),xytext=(x1,y1),arrowprops=dict(arrowstyle='<->',lw=0.8,color='#2f6e8f'),zorder=9)
    ax.text((x0+x1)/2+off[0],(y0+y1)/2+off[1],t,fontsize=8,color='#2f6e8f',ha='center',va='center',zorder=9,bbox=dict(fc='white',ec='none',pad=1))
dim(0,-10,PW,-10,'overlay 302.5 mm')
dim(-10,0,-10,PH,'228.8 mm',off=(0,0))
dim(KX0,KY0-3.5,KX1,KY0-3.5,'keyboard 286 mm')
ax.set_xlim(-35,PW+25); ax.set_ylim(-34,PH+42); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('Lid, top view to scale: keyboard under the overlay, accessory tray and cable slot',fontsize=11,color=INK)
plt.tight_layout(); plt.savefig('../docs/lid_layout_render.png',facecolor='white')
print('ok')
