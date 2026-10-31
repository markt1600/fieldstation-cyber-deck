"""Draws ../docs/frame_v2.png: the v2 base frame (panel, pods, posts, pod brackets) with the floor plate pulled back,
showing the 12 screws that come up through the plate into the feet."""
import numpy as np
exec(open('case_render.py').read().split("NOLABEL=")[0])
GAP=70.0
keys=[('Base panel',0),('Speaker pods ×2',0),('Floor posts ×4',0),('Pod brackets ×2 (epoxied to the pods)',0),
      ('Floor plate (posts and brackets screw to it; taped to the case floor)',GAP)]
items=[]
for k,dz in keys:
    m,c,g=cache[k]; t=m.copy(); t.apply_translation([0,0,dz]); items.append((t,c))
holes=[h for n in F['POSTS'] for h in F['foot_holes'](n)]+[h for k in FP['POD_BRK'] for h in FP['brk_holes'](k)]
fig=plt.figure(figsize=(18,12.5),dpi=100)
for i,(view,title) in enumerate([((-0.75,0.6,0.85),'Seen from behind: the plate (pulled back) screws up into the post feet and pod brackets')]):
    img,proj=render(items,view=view,up=(0,1,0),W=1700,H=1150,margin=60,lh=True)
    ax=fig.add_axes([0.02,0.02,0.96,0.86]); ax.imshow(img); ax.set_axis_off(); ax.set_title(title,fontsize=13,loc='left',pad=4)
    if i==0:
        for hx,hy in holes:
            q=proj(np.array([[hx,hy,FLOOR_Z-FP['FP_T']],[hx,hy,FLOOR_Z+GAP+12]]))
            ax.plot(q[:,0],q[:,1],ls=(0,(4,3)),lw=1.0,color='#c1121f')
        q=proj(np.array([150,150,FLOOR_Z+GAP]))[0]
        ax.annotate('floor plate (2 pieces, dovetailed)',xy=q,xytext=(q[0]-330,q[1]+330),fontsize=11,arrowprops=dict(arrowstyle='-',color='#555'),bbox=dict(fc='white',ec='#c9cdd2'))
        for lab,pt in [('post feet: 2 inserts each',[26,215,FLOOR_Z-6]),('pod brackets: 2 inserts each',[77,97,FLOOR_Z-6]),('speaker pods',[52,8,40]),('base panel',[150,228,0])]:
            q=proj(np.array(pt))[0]
            ax.annotate(lab,xy=q,xytext=(q[0]+40,q[1]-50),fontsize=11,arrowprops=dict(arrowstyle='-',color='#555'),bbox=dict(fc='white',ec='#c9cdd2'))
fig.text(0.02,0.985,'Base frame v2: everything screws to the floor plate',fontsize=20,weight='bold',va='top')
fig.text(0.02,0.955,'Red dashed lines: 12 × M3 × 8 countersunk screws, up through the plate into heat-set inserts in the 4 post feet and 2 pod brackets. Then VHB under the plate and the whole frame drops into the case.',fontsize=11,color='#444',va='top')
fig.savefig('../docs/frame_v2.png',facecolor='white'); print('saved')
