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
_mv=lambda m: m.mirror([1,0,0]).translate([AIR_C[0],AIR_C[1],T])   # cradle is mirrored on the right
_air=_S['body']
for _m in _S['board_parts']()[1:]: _air=_air+_m       # adapter board, connector, Dupont plugs
_air=_air+box(-5,24,4,5,36,_S['SNOUT'])      # wires leaving the end-wall slot
parts['air']=_mv(_air)
# screen plugs on its left edge (measured from a photo): micro-USB 30-39 mm and HDMI 47-65 mm up from the
# screen's bottom edge, ~40 mm long straight plugs, then the cables turn up/back beside the screen
parts['screen_plugs']=box(SC_X0-42,SC_Y0+26,T+1,SC_X0,SC_Y0+69,T+SC_T)+box(SC_X0-48,SC_Y0+26,T+SC_T,SC_X0-14,SC_Y0+97,T+44)
# KVM is stuck to the back of the screen: VHB 1.1 + 2 mm printed spacer + VHB 1.1 brings it to z 25, clear of the clamps (to z 23.7)
parts['kvm_spacer']=box(67,125,T+SC_T+1.1,127,185,T+SC_T+3.1)
parts['kvm']=box(42,114,25,139,205,48)+box(60,205,25,121,223,48)+box(55,89,25,126,114,48)   # body, right-angle console plugs, host-cable bend
for n in POSTS: parts['post'+n]=build_post(n).mirror([0,0,1]).translate([0,0,FLOOR_Z-VHB])
# Pi case on floor, right half behind screen; breakout + 70 x 50 soldered perfboard left half
# perfboard: on the floor plate (3 mm) + 6 mm bosses, 1.6 mm board, 15 mm kept clear above it for the soldered wires
_FP={'__name__':'lib'}; exec(open('floorplate.py').read().split("if __name__")[0],_FP)
parts['floor_plate']=_FP['build_floor_plate']()
# boards sit on the floor plate (3 mm); the Pi in its pocket, the boards on 6 mm bosses
parts['pi']=box(145,105,FLOOR_Z-3-62.75,145+98.75,105+90.2,FLOOR_Z-3)
# breakout turned 90 deg: 55 x 65; 35 mm from the plate, incl. parts under the board around its 9 mm bosses
_BO=_FP["BO"]
parts["breakout"]=box(_BO[0],_BO[1],FLOOR_Z-3-35,_BO[2],_BO[3],FLOOR_Z-12)+(box(_BO[0],_BO[1],FLOOR_Z-12,_BO[2],_BO[3],FLOOR_Z-3)-parts["floor_plate"])
_PB=_FP['PB']
parts['breadboard']=box(_PB[0],_PB[1],FLOOR_Z-9-1.6-15,_PB[2],_PB[3],FLOOR_Z-9)
names=list(parts); bad=0
for i in range(len(names)):
    for j in range(i+1,len(names)):
        v=(parts[names[i]]^parts[names[j]]).volume()
        if v>0.5: print('CLASH',names[i],names[j],round(v,1),'mm3'); bad+=1
print('clashes:',bad)
print('pod back to floor gap %.1f mm'%(FLOOR_Z-(T+POD_DEPTH)))
print('pi top to screen back gap %.1f mm'%((FLOOR_Z-3-62.75)-(T+SC_T)))
print('tray floor back face %.1f mm behind panel front; rim-to-tray-back %.1f'%(PK_DEPTH+3, RIM_DROP+PK_DEPTH+3))

# posts' feet must sit on the flat floor: >= ~18 mm in from the wall line at panel height (wall ~1.7 mm outside panel edge)
for n,(x,y) in POSTS.items():
    b=to_tm(build_post(n)).bounds
    print('post',n,'foot clearance from walls: x %.1f / %.1f, y %.1f / %.1f'%(b[0][0]+1.7,PW-b[1][0]+1.7,b[0][1]+1.7,PH-b[1][1]+1.7))
