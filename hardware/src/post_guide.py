"""Draws ../docs/post_guide.png: where each of the four floor posts goes and which way its foot points."""
import numpy as np, trimesh
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from raster import render
g={'__name__':'lib'}; exec(open('frame.py').read(),g)
PW,PH,POSTS=g['PW'],g['PH'],g['POSTS']
SC=(g['SC_X0'],g['SC_Y0'],g['SC_W'],g['SC_H'])
def tm(m): o=m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:,:3],o.tri_verts,process=False)
def foot(n):
    x,y=POSTS[n]; fx0,fx1=(x-5,x+21) if x<PW/2 else (x-21,x+5); fy0,fy1=(y-13,y+5) if n in ('TL','TR') else (y-5,y+5)
    return fx0,fy0,fx1,fy1
NAMES={'TL':'top left','TR':'top right','ML':'lower left','MR':'lower right'}
COL={'TL':'#e63946','TR':'#2a9d8f','ML':'#f4a261','MR':'#457b9d'}
fig=plt.figure(figsize=(17,13))
def panel_view(ax,mirror,title):
    X=(lambda x:PW-x) if mirror else (lambda x:x)
    ax.add_patch(FancyBboxPatch((0,0),PW,PH,boxstyle='round,pad=0,rounding_size=19',fc='#e9ecef',ec='k'))
    ax.add_patch(Rectangle((X(SC[0]+SC[2]) if mirror else SC[0],SC[1]),SC[2],SC[3],fc='#1d3557',alpha=0.25,ec='#1d3557'))
    ax.text(PW/2,SC[1]+SC[3]/2,'screen',ha='center',va='center',color='#1d3557')
    for n,(x,y) in POSTS.items():
        fx0,fy0,fx1,fy1=foot(n); a,b=sorted([X(fx0),X(fx1)])
        ax.add_patch(Rectangle((a,fy0),b-a,fy1-fy0,fc=COL[n],alpha=0.35,ec=COL[n],ls='--'))
        ax.add_patch(Rectangle((X(x)-5,y-5),10,10,fc=COL[n],ec='k'))
        cx=(a+b)/2; ax.annotate('',xy=(cx+(b-a)*0.35*np.sign(cx-X(x)),(fy0+fy1)/2),xytext=(X(x),(fy0+fy1)/2),arrowprops=dict(arrowstyle='->',color='k',lw=1.2))
        ax.text(X(x),y+9,n,ha='center',fontsize=12,weight='bold',color=COL[n])
    ax.set_xlim(-8,PW+8); ax.set_ylim(-8,PH+8); ax.set_aspect('equal'); ax.set_title(title,fontsize=12); ax.set_xticks([]); ax.set_yticks([])
ax1=fig.add_axes([0.02,0.38,0.47,0.48]); panel_view(ax1,False,'Seen from the FRONT (through the panel)\nsquares = post columns, dashed = feet on the case floor')
ax2=fig.add_axes([0.51,0.38,0.47,0.48]); panel_view(ax2,True,'Panel FACE DOWN on the bench (how you screw them on)\nleft and right swap: TL is now at the top right')
for i,n in enumerate(['TL','TR','ML','MR']):
    img,proj=render([(tm(g['build_post'](n)),(0.62,0.66,0.70))],view=(0.15,-1.0,0.55),up=(0,0,1),W=420,H=520,margin=20)
    ax=fig.add_axes([0.02+i*0.245,0.02,0.22,0.30]); ax.imshow(img); ax.set_axis_off()
    x,y=POSTS[n]
    side='right' if x<PW/2 else 'left'; extra=' and down' if n in ('TL','TR') else ''
    ax.set_title('%s: %s\nfoot reaches %s%s (toward the middle)'%(n,NAMES[n],side,extra),fontsize=11,color=COL[n])
fig.text(0.02,0.975,'FLOOR POSTS: where each one goes',fontsize=18,weight='bold',va='top')
fig.text(0.02,0.952,'Each post screws to the back of the panel (M3 × 10 from the front) and stands on the case floor on VHB.\nEvery foot points in toward the middle of the case, away from the curved floor edge. Bottom row: each post standing on its foot, viewed from the bottom edge of the case.',fontsize=10.5,va='top',color='#444')
fig.savefig('../docs/post_guide.png',dpi=90)
print('wrote ../docs/post_guide.png')
