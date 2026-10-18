exec(open('frame.py').read())
def box(x0,y0,z0,x1,y1,z1): return Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
FLOOR_Z=BASE_DEPTH-RIM_DROP
parts={}
for i,(cx,cy) in enumerate(PODS): parts[f'pod{i}']=box(cx-40,cy-40,T,cx+40,cy+40,T+POD_DEPTH)
parts['screen']=box(SC_X0,SC_Y0,T,SC_X0+SC_W,SC_Y0+SC_H,T+SC_T)
cl=None
for cx,cy,sx,sy in [(SC_X0,SC_Y0,1,1),(SC_X0+SC_W,SC_Y0,-1,1),(SC_X0,SC_Y0+SC_H,1,-1),(SC_X0+SC_W,SC_Y0+SC_H,-1,-1)]:
    a=box(min(cx-sx*9,cx+sx*24),min(cy-sy*9,cy),T,max(cx-sx*9,cx+sx*24),max(cy-sy*9,cy),T+19.7)
    b=box(min(cx-sx*9,cx),min(cy-sy*9,cy+sy*24),T,max(cx-sx*9,cx),max(cy-sy*9,cy+sy*24),T+19.7)
    cl=(a+b) if cl is None else cl+a+b
parts['clamps']=cl
parts['tray']=build_tray()
_S={'__name__':'lib'}; exec(open('pms7003_v2.py').read().split("o=body.to_mesh()")[0],_S)
_mv=lambda m: m.translate([AIR_C[0],AIR_C[1],T])
_air=_S['body']
for _m in _S['board_parts']()[1:]: _air=_air+_m       # adapter board, connector, Dupont plugs
# room for the wires to bend away from the plug ends
_air=_air+box(6,11,8,20,34,_S['SNOUT']+_S['BRD_BACK'])
parts['air']=_mv(_air)
for n in POSTS: parts['post'+n]=build_post(n).mirror([0,0,1]).translate([0,0,FLOOR_Z-VHB])
# Pi case on floor, right half behind screen; breakout + mini breadboard left half
parts['pi']=box(145,105,FLOOR_Z-62.75,145+98.75,105+90.2,FLOOR_Z)
parts['breakout']=box(60,140,FLOOR_Z-25,60+65,140+56.2,FLOOR_Z)
parts['breadboard']=box(70,105,FLOOR_Z-10,70+46.4,105+34.5,FLOOR_Z)
names=list(parts); bad=0
for i in range(len(names)):
    for j in range(i+1,len(names)):
        v=(parts[names[i]]^parts[names[j]]).volume()
        if v>0.5: print('CLASH',names[i],names[j],round(v,1),'mm3'); bad+=1
print('clashes:',bad)
print('pod back to floor gap %.1f mm'%(FLOOR_Z-(T+POD_DEPTH)))
print('pi top to screen back gap %.1f mm'%((FLOOR_Z-62.75)-(T+SC_T)))
print('tray floor back face %.1f mm behind panel front; rim-to-tray-back %.1f'%(PK_DEPTH+3, RIM_DROP+PK_DEPTH+3))

# posts' feet must sit on the flat floor: >= ~18 mm in from the wall line at panel height (wall ~1.7 mm outside panel edge)
for n,(x,y) in POSTS.items():
    b=to_tm(build_post(n)).bounds
    print('post',n,'foot clearance from walls: x %.1f / %.1f, y %.1f / %.1f'%(b[0][0]+1.7,PW-b[1][0]+1.7,b[0][1]+1.7,PH-b[1][1]+1.7))
