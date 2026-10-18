import numpy as np, trimesh
def render(items, view=(1,-1.2,0.9), up=(0,0,1), W=1400, H=1000, margin=40, light=(0.4,-0.6,0.9), bg=(1,1,1)):
    """items: list of (trimesh, rgb(0-1)). Orthographic z-buffer render with flat shading and outline edges.
    Returns image (H,W,3) and a project(points)->pixel function."""
    v=np.array(view,float); v/=np.linalg.norm(v)
    u=np.array(up,float); r=np.cross(u,v); r/=np.linalg.norm(r); u2=np.cross(v,r)
    allv=np.vstack([m.vertices for m,_ in items])
    P=np.c_[allv@r, allv@u2]
    mn,mx=P.min(0),P.max(0); s=min((W-2*margin)/(mx[0]-mn[0]),(H-2*margin)/(mx[1]-mn[1]))
    off=np.array([(W-(mx[0]-mn[0])*s)/2,(H-(mx[1]-mn[1])*s)/2])
    def proj(p):
        p=np.atleast_2d(p); q=np.c_[p@r,p@u2]; x=(q[:,0]-mn[0])*s+off[0]; y=H-((q[:,1]-mn[1])*s+off[1]); return np.c_[x,y]
    img=np.ones((H,W,3))*np.array(bg); zb=np.full((H,W),-1e18); nid=np.full((H,W),-1,int)
    L=np.array(light,float); L/=np.linalg.norm(L)
    fid=0
    for mi,(m,col) in enumerate(items):
        V=m.vertices; F=m.faces; N=m.face_normals
        xy=proj(V); dep=V@v
        shade=0.35+0.65*np.clip(N@L,0,1)*0.85+0.15*np.clip(N@v,0,1)
        for k,(a,b,c) in enumerate(F):
            if N[k]@v<=0: continue                      # back-face cull (camera looks along -v)
            p0,p1,p2=xy[a],xy[b],xy[c]
            x0=int(max(min(p0[0],p1[0],p2[0]),0)); x1=int(min(max(p0[0],p1[0],p2[0])+1,W-1))
            y0=int(max(min(p0[1],p1[1],p2[1]),0)); y1=int(min(max(p0[1],p1[1],p2[1])+1,H-1))
            if x1<x0 or y1<y0: continue
            den=(p1[1]-p2[1])*(p0[0]-p2[0])+(p2[0]-p1[0])*(p0[1]-p2[1])
            if abs(den)<1e-9: continue
            X,Y=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
            w0=((p1[1]-p2[1])*(X-p2[0])+(p2[0]-p1[0])*(Y-p2[1]))/den
            w1=((p2[1]-p0[1])*(X-p2[0])+(p0[0]-p2[0])*(Y-p2[1]))/den
            w2=1-w0-w1
            inside=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
            if not inside.any(): continue
            z=w0*dep[a]+w1*dep[b]+w2*dep[c]
            sub=zb[y0:y1+1,x0:x1+1]; upd=inside&(z>sub)
            if not upd.any(): continue
            sub[upd]=z[upd]
            img[y0:y1+1,x0:x1+1][upd]=np.clip(np.array(col)*shade[k],0,1)
            nid[y0:y1+1,x0:x1+1][upd]=mi*1000003+int(np.round(N[k][0]*3))*49+int(np.round(N[k][1]*3))*7+int(np.round(N[k][2]*3))
    # outlines: object or normal-group changes, and depth steps
    edge=np.zeros((H,W),bool)
    for dy,dx in ((0,1),(1,0)):
        a=nid; b=np.roll(np.roll(nid,dy,0),dx,1)
        edge|=(a!=b)
        za=zb; zbb=np.roll(np.roll(zb,dy,0),dx,1)
        edge|=(np.abs(za-zbb)>3.0/s*1.0)&(za>-1e17)
    img[edge]=img[edge]*0.35
    return img,proj
