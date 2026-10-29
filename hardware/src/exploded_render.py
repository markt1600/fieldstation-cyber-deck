"""Draws ../docs/exploded_base.png: one large exploded view of the base, numbered in assembly order."""
import numpy as np, time
exec(open('case_render.py').read().split("NOLABEL=")[0])
ORDER=[('Base panel',-270,0,'Base panel (front face toward you)'),
       ('Port tray',0,0,'Port tray + controls'),('Speaker pods ×2',0,0,'Speaker pods ×2 (front-mounted drivers)'),
       ('PMS7003 cradle',0,0,'PMS7003 cradle'),('PMS7003 + adapter board',0,0,None),
       ('Screen (7" in case)',0,10,'Screen in its case'),('Screen clamps ×4',55,20,'Screen clamps ×4'),
       ('Floor posts ×4',205,25,'Floor posts ×4 (M3 × 10 from the front)'),
       ('Pod brackets ×2 (epoxied to the pods)',245,10,'Pod brackets ×2 (epoxied to the pods)'),
       ('Pi 5 in X1202 case',300,80,'Pi 5 in X1202 case (strapped into its pocket)'),
       ('GPIO breakout (turned 90°)',350,95,'GPIO breakout'),('Soldered perfboard',350,95,'Soldered perfboard'),
       ('Floor plate (posts and brackets screw to it; taped to the case floor)',450,125,'Floor plate (12 × M3 × 8 csk up into the feet)'),
       ('Peli 1400 base',660,200,'Peli 1400 base (VHB under the plate)')]
items=[];num=[];legend=[]
n=0
for k,dz,dy,lab in ORDER:
    m,c,g=cache[k]; t=m.copy(); t.apply_translation([0,dy,dz]); items.append((t,c))
    if lab:
        n+=1; b=t.bounds; c0=np.array([(b[0][0]+b[1][0])/2,b[1][1],(b[0][2]+b[1][2])/2]); v=t.vertices[np.argmin(((t.vertices-c0)**2).sum(1))]; num.append((n,list(v))); legend.append('%d  %s'%(n,lab))
t0=time.time(); img,proj=render(items,view=(-0.9,0.55,-0.75),up=(0,1,0),W=2000,H=1500,margin=60,lh=True); print('render %.0fs'%(time.time()-t0))
fig=plt.figure(figsize=(20,17),dpi=100)
ax=fig.add_axes([0.0,0.13,1.0,0.80]); ax.imshow(img); ax.set_axis_off()
used=[]
for i,(k,pt) in enumerate(num):
    q=proj(np.array(pt))[0]; tx,ty=q[0],q[1]-45
    for ux,uy in used:
        if abs(ux-tx)<40 and abs(uy-ty)<40: ty-=45
    used.append((tx,ty))
    ax.annotate(str(k),xy=q,xytext=(tx,ty),ha='center',va='center',fontsize=13,weight='bold',color='white',
                bbox=dict(boxstyle='circle,pad=0.35',fc='#c1121f',ec='white'),arrowprops=dict(arrowstyle='-',lw=1,color='#c1121f'))
fig.text(0.02,0.975,'FIELDSTATION base, exploded in assembly order',fontsize=22,weight='bold',va='top')
fig.text(0.02,0.95,'Front of the panel at the right, case at the left. Build the frame (1–12) outside the case, then lower it in as one piece.',fontsize=12,color='#444',va='top')
cols=3; per=int(np.ceil(len(legend)/cols))
for ci in range(cols):
    fig.text(0.03+ci*0.32,0.11,'\n'.join(legend[ci*per:(ci+1)*per]),fontsize=12,va='top',family='monospace',linespacing=1.7)
fig.savefig('../docs/exploded_base.png',facecolor='white'); print('saved')
