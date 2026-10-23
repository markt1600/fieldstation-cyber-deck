// Trend of the gauge's reported state of charge; never an amperage estimate.
function batteryChargeTrend(history,now=Date.now()/1000){
 const rows=[...new Map(history.filter(x=>Number.isFinite(x.timestamp)&&Number.isFinite(x.reported_percent)&&x.reported_percent>=0&&x.reported_percent<=100&&x.timestamp>=now-1800&&x.timestamp<=now).map(x=>[x.timestamp,x])).values()].sort((a,b)=>a.timestamp-b.timestamp);
 if(rows.length<10||now-rows.at(-1).timestamp>90)return null;
 const span=rows.at(-1).timestamp-rows[0].timestamp;if(span<600)return null;
 if(rows.some((r,i)=>i&&r.timestamp-rows[i-1].timestamp>180))return null;
 const xs=rows.map(r=>(r.timestamp-rows[0].timestamp)/3600),ys=rows.map(r=>r.reported_percent),mx=xs.reduce((a,b)=>a+b,0)/xs.length,my=ys.reduce((a,b)=>a+b,0)/ys.length;
 const numerator=xs.reduce((sum,x,i)=>sum+(x-mx)*(ys[i]-my),0),denominator=xs.reduce((sum,x)=>sum+(x-mx)**2,0);
 return {pointsPerHour:numerator/denominator,minutes:Math.round(span/60)};
}
let energyBuilt=false,energyPending=false;
function renderLiveEnergy(){
 if(!energyBuilt){
  energyBuilt=true;
  document.querySelector('#energy').innerHTML=`<div class="energy-status"><span class="badge" id="battery-status">CONNECTING</span><span id="battery-power"></span><span id="battery-age" role="status">Reading X1202…</span></div>
  <p class="battery-note">Runtime uses the October 17 discharge test: screen on, amplifier off. A 3.40 V reporting reserve excludes the deeply discharged tail; this is not an automatic shutdown setting. Different loads change runtime. Displayed charge uses a 4.17 V full anchor and the measured discharge curve down to the 3.40 V usable reserve. This is an estimate of usable runtime, not measured stored energy. Raw UPS readings remain below for comparison. While plugged in, 100% means estimated full, not confirmed charge completion.</p>
  <div class="energy-grid"><article class="metric"><span>Estimated usable charge</span><div class="reading"><span id="battery-percent">—</span> <small>%</small></div><p>4.17 V = 100% · 3.40 V = 0% usable reserve</p></article>
  <article class="metric"><span>Raw UPS charge</span><div class="reading"><span id="battery-raw-percent">—</span> <small>%</small></div><p>Unchanged fuel-gauge reading · separate from calibrated display</p></article>
  <article class="metric"><span>Battery voltage</span><div class="reading"><span id="battery-voltage">—</span> <small>V</small></div><p>Live X1202 gauge reading</p></article>
  <article class="metric"><span>Reported charge trend</span><div class="reading"><span id="battery-rate">—</span> <small>points/hour</small></div><p id="battery-rate-note">Needs 10 minutes of recent readings</p><p>Gauge trend only · not measured amps or watts</p></article>
  
  
  
  <article class="metric"><span>Estimated time to full*</span><div class="reading" id="battery-charge-duration">—</div><p id="battery-charge-note"></p></article>
  <article class="metric"><span>Estimated full-charge time</span><div class="reading" id="battery-charge-clock">—</div><p>Local time · recorded near-full charge level, not charger confirmation</p></article>
  <article class="metric"><span>Time remaining to reserve</span><div class="reading" id="battery-runtime">—</div><p id="battery-runtime-note"></p></article></div>
  <p class="battery-note">*Charging estimates use the October 18 recharge curve and its observed near-full region (about 98% raw UPS charge). Unlike the voltage-based display, this model includes the charging taper. It is not a verified charger-completion time. Discharge runtime uses the separate measured discharge curve.</p><section class="battery-history"><h2>Recent battery readings</h2><p>Samples every 5 seconds; saves a reading every 30 seconds. Saved history survives restarts. Sampling runs while Fieldstation is on.</p><p id="battery-log-status" role="status"></p><p id="battery-trend"></p><table><thead><tr><th>Time</th><th>Voltage</th><th>Reported charge</th></tr></thead><tbody id="battery-history"></tbody></table></section>`;
 }
 refreshBattery();
}
async function refreshBattery(){
 if(energyPending)return;
 if(!energyBuilt){renderLiveEnergy();return;}
 energyPending=true;
 try{
  const r=await fetch('/api/battery',{signal:AbortSignal.timeout(4000),cache:'no-store'});
  if(!r.ok)throw Error();const d=await r.json(),live=d.status==='live'&&d.readings;
  updateBatterySummary(d);
  updateChargeEstimate(d);
  document.querySelector('#battery-power').textContent=d.external_power===true?'⚡ Plugged in':d.external_power===false?'On battery':'Power source unknown';
  document.querySelector('#battery-status').textContent=live?'LIVE · UNVERIFIED':d.status==='stale'?'STALE':'UNAVAILABLE';
  document.querySelector('#battery-age').textContent=d.age_seconds===null?'Waiting for the battery gauge':(live?'Updated ':'Last successful reading ')+Math.round(d.age_seconds)+' seconds ago';
  const estimated=live?usableBatteryPercent(d.readings.voltage_v):null;
  document.querySelector('#battery-percent').textContent=estimated===null?'—':estimated.toFixed(0);
  document.querySelector('#battery-raw-percent').textContent=live&&Number.isFinite(d.readings.reported_percent)?d.readings.reported_percent.toFixed(2):'—';
  document.querySelector('#battery-voltage').textContent=live?d.readings.voltage_v.toFixed(2):'—';
  const trend=live?batteryChargeTrend(d.history||[]):null;
  document.querySelector('#battery-rate').textContent=trend?(trend.pointsPerHour>=0?'+':'')+trend.pointsPerHour.toFixed(1):'—';
  document.querySelector('#battery-rate-note').textContent=trend?`${Math.abs(trend.pointsPerHour)<.2?'Nearly steady':trend.pointsPerHour>0?'Rising':'Falling'} over the last ${trend.minutes} minutes. External power and gauge corrections affect this trend.`:'Needs 10 minutes of continuous recent readings';
  const h=d.history||[],tbody=document.querySelector('#battery-history');tbody.replaceChildren();
  const tracking=d.tracking||{};
  document.querySelector('#battery-log-status').textContent=tracking.error|| (tracking.started_at?`${tracking.saved_samples} records saved since ${new Date(tracking.started_at*1000).toLocaleString()}`:'Starting persistent log…');
  h.slice(-8).reverse().forEach(v=>{const tr=document.createElement('tr');[new Date(v.timestamp*1000).toLocaleTimeString(),v.voltage_v.toFixed(2)+' V',v.reported_percent.toFixed(2)+'%'].forEach(t=>{const td=document.createElement('td');td.textContent=t;tr.append(td)});tbody.append(tr)});
  const change=h.length>1?h.at(-1).voltage_v-h[0].voltage_v:null;
  document.querySelector('#battery-trend').textContent=change===null?'Collecting readings…':`Voltage change over ${Math.round((h.at(-1).timestamp-h[0].timestamp)/60)} minutes: ${change>=0?'+':''}${change.toFixed(2)} V`;
 }catch{
  updateBatterySummary({status:'unavailable'});
  updateChargeEstimate({status:'unavailable'});
  document.querySelector('#battery-power').textContent='Power source unknown';
  document.querySelector('#battery-status').textContent='UNAVAILABLE';document.querySelector('#battery-age').textContent='Could not refresh battery readings';
  document.querySelector('#battery-rate').textContent='—';
  document.querySelector('#battery-rate-note').textContent='No recent readings';
  document.querySelector('#battery-raw-percent').textContent='—';document.querySelector('#battery-percent').textContent='—';document.querySelector('#battery-voltage').textContent='—';
 }finally{energyPending=false;}
}
setInterval(refreshBattery,5000);

// Measured elapsed minutes / voltage, screen on and amplifier off.
// Upper anchor calibrated to the observed near-full recharge plateau; no extra runtime added.
const dischargeCurve=[[0,4.17],[16.60,4.0462],[31.61,4.0275],[50.21,4.01],[66.14,3.9813],[81.57,3.9375],[97.08,3.8887],[112.59,3.845],[128.11,3.815],[143.62,3.78],[159.13,3.7575],[174.64,3.7175],[190.82,3.6612],[206.25,3.6175],[221.59,3.56],[237.11,3.5088],[252.62,3.455],[268.14,3.4112],[283.65,3.3325]];
function measuredElapsed(voltage){
 if(voltage>=dischargeCurve[0][1])return 0;
 for(let i=1;i<dischargeCurve.length;i++){const [t,v]=dischargeCurve[i],[pt,pv]=dischargeCurve[i-1];if(voltage>=v)return pt+(pv-voltage)/(pv-v)*(t-pt);}
 return dischargeCurve.at(-1)[0];
}
function usableBatteryPercent(voltage){
 if(!Number.isFinite(voltage))return null;
 const total=measuredElapsed(3.40);
 return Math.max(0,Math.min(100,100*(total-measuredElapsed(voltage))/total));
}
function batteryRuntime(d,now=Date.now()/1000){
 const r=d.readings;
 if(d.status!=='live'||!r||!Number.isFinite(r.voltage_v)||!Number.isFinite(r.timestamp)||Math.abs(now-r.timestamp)>90)return {text:'Unavailable',note:'Waiting for fresh battery readings'};
 const rows=(d.history||[]).filter(x=>Number.isFinite(x.voltage_v)&&x.timestamp>=now-900&&x.timestamp<=now).sort((a,b)=>a.timestamp-b.timestamp);
 const continuous=rows.length>=10&&rows.at(-1).timestamp-rows[0].timestamp>=600&&!rows.some((x,i)=>i&&x.timestamp-rows[i-1].timestamp>90);
 const falling=d.external_power!==true&&continuous&&rows.at(-1).voltage_v-rows[0].voltage_v<-.005;
 if(r.voltage_v<=3.4)return {text:'<5 min',note:'Below 3.40 V reporting reserve · keep external power connected'};
 const minutes=Math.max(0,measuredElapsed(3.4)-measuredElapsed(r.voltage_v));
 const rounded=Math.round(minutes/5)*5;
 return {text:rounded<5?'<5 min':`≈ ${Math.floor(rounded/60)}h ${rounded%60}m`,note:falling?'To 3.40 V reserve · screen on, amp off · approximate':'Provisional battery-only runtime · charging voltage may overestimate · screen on, amp off'};

}
function updateBatterySummary(d){
 const model=batteryRuntime(d),live=d.status==='live'&&d.readings&&Number.isFinite(d.readings.voltage_v)&&Math.abs(Date.now()/1000-d.readings.timestamp)<90;
 let box=document.querySelector('#home-battery');
 if(!box){box=document.createElement('section');box.id='home-battery';box.className='rail-power';box.setAttribute('aria-label','Battery and external power');document.querySelector('.brand')?.after(box);}
 if(box){box.replaceChildren();const content=document.createElement('div'),title=document.createElement('strong'),note=document.createElement('p'),button=document.createElement('button');title.textContent=live?`${d.external_power===true?'⚡ ':''}${usableBatteryPercent(d.readings.voltage_v).toFixed(0)}% · ${d.readings.voltage_v.toFixed(2)} V · ${model.text}`:'Battery unavailable';note.textContent=(d.external_power===true?'Plugged in · ':d.external_power===false?'On battery · ':'Power unknown · ')+(model.note.startsWith('Provisional')?'provisional runtime':'to reserve');box.title='Estimated usable charge · 4.17 V full / 3.40 V reserve · '+model.note+(live?' · '+d.readings.voltage_v.toFixed(2)+' V':'');button.textContent='Energy →';button.onclick=()=>go('energy');content.append(title,note);box.append(content,button);}
 const runtime=document.querySelector('#battery-runtime'),note=document.querySelector('#battery-runtime-note');if(runtime)runtime.textContent=model.text;if(note)note.textContent=model.note;
}

setTimeout(refreshBattery,0);

// October 18 recharge: [elapsed minutes, raw UPS percentage].
// First observed crossings, deduplicated from saved 30-second samples. Loads varied.
// 98.133% is the observed near-full point, not a charger termination signal.
const rechargeCurve=[[94.91,.102],[111.92,1],[143.45,3.023],[154.96,5.062],[174.16,10.258],[196.22,20.09],[212.24,30.402],[225.17,40.105],[237.19,50.012],[249.2,60.109],[262.22,70.117],[276.24,80.258],[283.75,85.195],[293.76,90.066],[310.28,95.129],[328.31,98.133]];
function rechargeElapsed(percent){
 if(percent<=rechargeCurve[0][1])return rechargeCurve[0][0];
 for(let i=1;i<rechargeCurve.length;i++){
  const [t,p]=rechargeCurve[i],[pt,pp]=rechargeCurve[i-1];
  if(percent<=p)return pt+(percent-pp)/(p-pp)*(t-pt);
 }
 return rechargeCurve.at(-1)[0];
}
function batteryChargeETA(d,now=Date.now()/1000){
 const result=(text,note,minutes=null)=>({text,note,minutes,finish:minutes===null?null:now+minutes*60});
 const r=d.readings;
 if(d.status!=='live'||!r||!Number.isFinite(r.reported_percent)||!Number.isFinite(r.voltage_v)||!Number.isFinite(r.timestamp)||Math.abs(now-r.timestamp)>90)
  return result('Unavailable','Waiting for fresh battery readings');
 if(d.external_power!==true)return result(d.external_power===false?'On battery':'Power unknown','Connect external power for a charging estimate');
 const p=r.reported_percent;
 if(p>=98.133||(p>=97.5&&r.voltage_v>=4.16&&r.voltage_v<=4.18))
  return result('Estimated full','Matches the recorded near-full region; actual charging completion is not reported');
 if(p<.102)return result('Learning rate','Gauge is near zero; the deep-discharge recovery phase is too uncertain for a completion time');
 const base=rechargeCurve.at(-1)[0]-rechargeElapsed(p);
 let scale=1,adjusted=false;
 const start=d.power_connected_since;
 if(Number.isFinite(start)&&start<=now){
  const history=(d.history||[]).filter(x=>x.timestamp>=start+600);
  const trend=batteryChargeTrend(history,now);
  if(trend&&trend.minutes>=20){
   if(trend.pointsPerHour<=.2)return result('No clear charge gain','The recent gauge trend is flat or falling; completion cannot be predicted reliably');
   const rows=history.filter(x=>x.timestamp>=now-1800&&x.timestamp<=now&&Number.isFinite(x.reported_percent)).sort((a,b)=>a.timestamp-b.timestamp);
   const first=rows[0],last=rows.at(-1);
   const progress=rechargeElapsed(last.reported_percent)-rechargeElapsed(first.reported_percent);
   if(progress>1){
    scale=(last.timestamp-first.timestamp)/60/progress;
    if(scale<.5||scale>3)return result('Trend unstable','Recent progress differs too much from the measured recharge curve');
    adjusted=true;
   }
  }
 }
 const minutes=Math.max(5,Math.ceil(base*scale/5)*5);
 return result(`≈ ${Math.floor(minutes/60)}h ${minutes%60}m`,
  (adjusted?'Measured recharge curve, adjusted for recent progress. ':'Measured recharge curve baseline; recent rate not yet established. ')+
  'Includes the observed taper near full. Approximate: workload, solar input and gauge corrections can change the time.',minutes);
}
function updateChargeEstimate(d){
 const estimate=batteryChargeETA(d);
 const duration=document.querySelector('#battery-charge-duration'),clock=document.querySelector('#battery-charge-clock'),note=document.querySelector('#battery-charge-note');
 if(duration)duration.textContent=estimate.text;
 if(note)note.textContent=estimate.note;
 if(clock){
  clock.textContent=estimate.finish===null?'—':'≈ '+new Date(estimate.finish*1000).toLocaleString([], {weekday:'short',hour:'numeric',minute:'2-digit'});
 }
}
