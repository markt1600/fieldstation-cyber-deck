const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ctx=vm.createContext({setInterval(){},setTimeout(){}});
vm.runInContext(fs.readFileSync(require('node:path').join(__dirname,'../dist/energy.js'),'utf8'),ctx);
const percent=v=>ctx.usableBatteryPercent(v);
assert.equal(percent(4.17),100);
assert.equal(percent(4.25),100);
assert.equal(percent(3.40),0);
assert.equal(percent(2.9),0);
assert.equal(percent(NaN),null);
let last=0;
for(let v=3.4;v<=4.2;v+=.001){const p=percent(v);assert.ok(p>=last&&p>=0&&p<=100);last=p;}
const now=Date.now()/1000;
assert.equal(ctx.batteryRuntime({status:'live',readings:{voltage_v:4.17,timestamp:now}},now).text,'≈ 4h 30m');
assert.equal(ctx.batteryRuntime({status:'stale',readings:{voltage_v:4.17,timestamp:now}},now).text,'Unavailable');
assert.equal(ctx.batteryRuntime({status:'live',readings:{voltage_v:4.17,timestamp:now-100}},now).text,'Unavailable');
assert.ok(percent(3.78)>45&&percent(3.78)<50);
console.log('Battery calibration endpoints, monotonic curve, runtime and stale readings passed.');
