"""
scripts/generate_appraisal_html.py
Generates appraisal_form.html with embedded dataset fallbacks and full client-side logic.
"""
import os
import json

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "data")

with open(os.path.join(data_dir, "faculty.json"), "r", encoding="utf-8") as f:
    fac_data = json.load(f)
with open(os.path.join(data_dir, "attendance.json"), "r", encoding="utf-8") as f:
    att_data = json.load(f)
with open(os.path.join(data_dir, "certificates.json"), "r", encoding="utf-8") as f:
    cert_data = json.load(f)

fac_json = json.dumps(fac_data, ensure_ascii=False)
att_json = json.dumps(att_data, ensure_ascii=False)
cert_json = json.dumps(cert_data, ensure_ascii=False)

TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RIT Faculty Self-Appraisal System</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
<style>
body{background:#f7f7f7;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#222}
.sheet{max-width:960px;margin:0 auto;padding:12px}
.hdr{background:#e9e9e9;text-align:center;padding:22px 10px;margin-bottom:18px}
.hdr h1{font-size:22px;margin:0}.hdr p{margin:4px 0 0}
h2.t{text-align:center;font-size:22px;font-weight:400;margin:14px 0}
.sec{color:#555;margin:14px 0 4px}
table{width:100%;border-collapse:collapse;background:#fff}
th,td{border:1px solid #ddd;padding:6px 8px;vertical-align:top;word-wrap:break-word;overflow-wrap:anywhere}
th{background:#f3f3f3}
input.form-control,select.form-select{font-size:13px;padding:2px 6px;max-width:260px}
.btn-reset{background:#d9534f;color:#fff}.btn-calc{background:#eee;color:#333;border:1px solid #ccc}
.btn-print{background:#0b6fbf;color:#fff}.btn-auto{background:#198754;color:#fff}
.bad{color:#b02a37}.ok{color:#146c43}.warn{color:#8a6d00}
#report{margin-top:26px}.tag{font-size:11px;background:#fff3cd;padding:1px 6px;border-radius:3px}
.pnum:after{content:"Page " counter(page)}
@media (max-width:640px){.rt{overflow-x:auto}.rt table{min-width:760px}}
@media print{
 @page{size:A4;margin:14mm;@bottom-center{content:"Page " counter(page) " of " counter(pages)}}
 body{background:#fff}.no-print{display:none!important}.sheet{max-width:none;padding:0}
 .hdr{background:#fff;border-bottom:1px solid #000}
 #report{page-break-before:always;break-before:page;margin-top:0}
 thead{display:table-header-group}tr{page-break-inside:avoid;break-inside:avoid}
 th,td{border:1px solid #444;font-size:10.5px}.rt{overflow:visible}.rt table{min-width:0}
 input,select{border:none!important;background:none!important;appearance:none;padding:0!important}
}
</style></head><body><div class="sheet">
<div class="hdr"><h1>Ramaiah Institute of Technology</h1><p>(Autonomous Institute, affiliated to VTU)</p></div>

<div id="secA">
<h2 class="t">Welcome to Self-Appraisal System</h2>
<div class="no-print mb-2" id="dataBar"></div>
<div class="mb-2">Annual Appraisal Form for the Year
 <input id="y1" class="form-control d-inline-block w-auto" size="5" maxlength="4" inputmode="numeric" placeholder="YYYY"> -
 <input id="y2" class="form-control d-inline-block w-auto" size="5" maxlength="4" inputmode="numeric" placeholder="YYYY">
 <div id="yErr" class="bad"></div></div>
<div class="sec">General Information</div>
<table>
<tr><td style="width:40%">Full Name</td><td><input id="name" class="form-control" list="facList" autocomplete="off" placeholder="Type, then pick from list">
 <datalist id="facList"></datalist><div id="match" class="text-muted small"></div></td></tr>
<tr><td>Department</td><td><input id="dept" class="form-control"></td></tr>
<tr><td>Designation</td><td><select id="desig" class="form-select"><option>Assistant Professor</option><option>Associate Professor</option><option>Professor</option></select></td></tr>
</table>
<div class="sec">Details of Activities</div>
<table><thead><tr><th style="width:60px">Sl. No.</th><th>Scoring Category</th><th style="width:220px">Number / Input</th></tr></thead><tbody>
<tr><td>16</td><td>No. of events participated outside the institute<br>(FDP/Seminar/Workshop/Conference)</td><td><input id="p16" type="number" min="0" step="1" class="form-control" placeholder="0"></td></tr>
<tr><td>17</td><td>No. of events participated inside the institute<br>(FDP/Seminar/Workshop/Conference)</td><td><input id="p17" type="number" min="0" step="1" class="form-control" placeholder="0"></td></tr>
<tr><td colspan="2">Total Score:</td><td><input id="tot" class="form-control" readonly></td></tr>
<tr><td colspan="2">* Bonus Score:</td><td><input id="bon" class="form-control" readonly></td></tr>
<tr><td colspan="2">Final Score:</td><td><input id="fin" class="form-control" readonly></td></tr>
</tbody></table>
<div id="scoreMsg" class="small warn mt-1"></div>
<div class="no-print d-flex flex-wrap gap-2 my-3">
 <button class="btn btn-sm btn-reset" id="bReset">Reset</button>
 <button class="btn btn-sm btn-calc" id="bCalc">Calculate</button>
 <button class="btn btn-sm btn-auto" id="bAuto">Autofill Appraisal Details</button>
 <button class="btn btn-sm btn-print ms-auto" id="bPrint">Print Appraisal Form and Verification Report</button>
</div>
<div id="msg" class="no-print" role="status"></div>
</div>

<div id="report"><h2 class="t" style="font-size:18px">Certificate Verification Summary Report</h2><div id="repBody" class="text-muted">Select a faculty member and click “Autofill Appraisal Details”.</div></div>
</div>

<script>
window.EMBEDDED_DATA = {
 faculty: __FAC_JSON__,
 attendance: __ATT_JSON__,
 certificates: __CERT_JSON__
};

/* ===== CONFIGURATION (edit for your project) ===== */
const CONFIG={
 // Expected JSON arrays.
 urls:{faculty:'data/faculty.json',attendance:'data/attendance.json',certificates:'data/certificates.json'},
 internalAliases:['ramaiah institute of technology','m.s. ramaiah institute of technology','msrit','rit','msrit bangalore'],
 // Appraisal period rule. null = NOT configured -> no date filtering is applied (and the user is told).
 period:null,
 // Official scoring rules. null = NOT configured -> scores are not calculated.
 scoring:null
};
const LS_KEY='ritAppraisal.v1';
const DATA={faculty:null,attendance:null,certificates:null,errors:{}};

/* ===== PURE LOGIC ===== */
const norm=s=>String(s==null?'':s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function classify(venue,cfg=CONFIG){const v=norm(venue);if(!v||v==='unknown'||v==='none'||v==='not available')return 'Unknown';return cfg.internalAliases.some(a=>v.includes(norm(a)))?'Internal':'External';}
const evKey=e=>e.eventId?'id:'+e.eventId:'n:'+norm(e.eventName)+'|'+(e.startDate||'');
function statusOf(s){const n=norm(s);return n==='valid'?'Valid':n==='invalid'?'Invalid':'Pending Review';}
function parseDate(d){
 if(!d)return null;
 const s=String(d).trim();
 const mIso=s.match(/^(\\d{4})-(\\d{1,2})-(\\d{1,2})$/);
 if(mIso)return new Date(Date.UTC(+mIso[1],+mIso[2]-1,+mIso[3]));
 const mDmy=s.match(/^(\\d{1,2})[\\/.-](\\d{1,2})[\\/.-](\\d{4})$/);
 if(mDmy)return new Date(Date.UTC(+mDmy[3],+mDmy[2]-1,+mDmy[1]));
 const t=new Date(s);
 return isNaN(t)?null:t;
}
function periodRange(y1,cfg=CONFIG){if(!cfg.period||!y1)return null;const p=cfg.period;
 const s=new Date(Date.UTC(y1,p.startMonth-1,p.startDay));const e=new Date(Date.UTC(y1+1,p.startMonth-1,p.startDay));return[s,e];}
function inPeriod(d,rng){if(!rng)return true;const t=parseDate(d);return t!==null&&t>=rng[0]&&t<rng[1];}
function fmtDates(a,b){return a?(b&&b!==a?a+' to '+b:a):'';}

function compute(fac,data,y1,cfg=CONFIG){
 const att=(data.attendance||[]).filter(a=>a.facultyId===fac.id);
 const certsAll=(data.certificates||[]).filter(c=>c.facultyId===fac.id);
 const ev=new Map();let dupEvents=0,dupCerts=0;
 const get=e=>{const k=evKey(e);if(!ev.has(k))ev.set(k,{key:k,name:e.eventName||'',venue:'',start:'',end:'',attended:null,cert:null});return ev.get(k);};
 for(const a of att){const e=get(a);if(e.attended!==null||e.hasAtt)dupEvents++;e.hasAtt=true;
  e.name=e.name||a.eventName;e.venue=e.venue||a.venue||'';e.start=e.start||a.startDate||'';e.end=e.end||a.endDate||'';
  if(a.attended===true)e.attended=true;else if(a.attended===false&&e.attended!==true)e.attended=false;}
 const rank={Valid:3,'Pending Review':2,Invalid:1};
 for(const c of certsAll){const e=get(c);const st=statusOf(c.status);
  if(e.cert){dupCerts++;if(rank[st]<=rank[e.cert.st])continue;}
  e.cert={c,st};e.name=e.name||c.eventName;e.venue=e.venue||c.venue||'';e.start=e.start||c.startDate||'';e.end=e.end||c.endDate||'';}
 const rng=periodRange(y1,cfg);let p16=0,p17=0;const rows=[];
 for(const e of ev.values()){
  const cls=classify(e.venue,cfg);let contrib,why='';
  if(cls==='Unknown'){contrib='Pending Classification';why='Event venue could not be established.';}
  else if(cfg.period&&!e.start){contrib='Pending Classification';why='Event dates require confirmation.';}
  else if(!inPeriod(e.start,rng)){contrib='Neither';why='Event falls outside the appraisal period.';}
  else if(cls==='Internal'){contrib='Point 17';p17++;}else{contrib='Point 16';p16++;}
  let st=null,reason='';
  if(e.cert){const c=e.cert.c;st=e.cert.st;
   if(c.reason)reason=c.reason;
   else if(st!=='Valid'){
    if(c.facultyName&&norm(c.facultyName)!==norm(fac.name))reason='Faculty name does not match the available faculty record.';
    else if(c.startDate&&e.hasAtt&&att.some(a=>evKey(a)===e.key&&a.startDate&&a.startDate!==c.startDate))reason='Certificate details conflict with the attendance record.';
    else if(!e.venue)reason='Event venue could not be established.';
    else if(!e.start)reason='Event dates require confirmation.';}}
  rows.push({name:e.name,venue:e.venue,dates:fmtDates(e.start,e.end),cls,st,reason,contrib,why});}
 const sub=rows.filter(r=>r.st);
 const stats={total:sub.length,valid:sub.filter(r=>r.st==='Valid').length,invalid:sub.filter(r=>r.st==='Invalid').length,pending:sub.filter(r=>r.st==='Pending Review').length};
 return{p16,p17,rows,stats,dupEvents,dupCerts,flagged:rows.filter(r=>r.contrib==='Pending Classification').length,periodApplied:!!rng};
}
function scoreCalc(p16,p17,cfg=CONFIG){
 const s=cfg.scoring;if(!s||typeof s.w16!=='number'||typeof s.w17!=='number')return null;
 let t=p16*s.w16+p17*s.w17;if(typeof s.max==='number')t=Math.min(t,s.max);
 const b=typeof s.bonus==='function'?s.bonus(p16,p17):0;return{total:t,bonus:b,final:t+b};
}
function validYears(a,b){if(!/^\\d{4}$/.test(a)||!/^\\d{4}$/.test(b))return 'Enter both years as 4 digits.';
 a=+a;b=+b;if(a<2000||a>2100)return 'Start year must be between 2000 and 2100.';if(b!==a+1)return 'End year must be the start year + 1.';return '';}
const validCount=v=>/^\\d+$/.test(String(v).trim());
if(typeof module!=='undefined')module.exports={compute,classify,scoreCalc,validYears,validCount,CONFIG,norm,parseDate,inPeriod};

/* ===== UI ===== */
if(typeof document!=='undefined'){
const $=id=>document.getElementById(id);
let state={facId:null,result:null};
const say=(t,cls='')=>{$('msg').innerHTML='<div class="alert alert-'+(cls||'secondary')+' py-2">'+t+'</div>';};

async function loadData(){
 DATA.errors={};
 for(const k of ['faculty','attendance','certificates']){
  try{
   const r=await fetch(CONFIG.urls[k]);
   if(!r.ok)throw new Error('HTTP '+r.status);
   const j=await r.json();
   if(!Array.isArray(j))throw new Error('not an array');
   DATA[k]=j;
  }
  catch(e){
   if(window.EMBEDDED_DATA&&Array.isArray(window.EMBEDDED_DATA[k])){
    DATA[k]=window.EMBEDDED_DATA[k];
   } else {
    DATA[k]=null;DATA.errors[k]=e.message;
   }
  }
 }
 renderBar();
}
function renderBar(){
 const names=['faculty','attendance','certificates'];
 $('dataBar').innerHTML=names.map(k=>DATA[k]?'<span class="ok">'+k+': '+DATA[k].length+' records</span>':'<span class="bad">'+k+': unavailable'+(DATA.errors[k]?' ('+esc(DATA.errors[k])+')':'')+'</span>').join(' &nbsp;|&nbsp; ')
  +' <button class="btn btn-sm btn-outline-secondary ms-2" id="bReload">Reload datasets</button>';
 $('bReload').onclick=()=>{loadData();};
 $('facList').innerHTML=(DATA.faculty||[]).map(f=>'<option value="'+esc(f.name)+'">' ).join('');
}
function resolveFaculty(){
 const v=$('name').value.trim();const list=DATA.faculty;
 if(!list)return{err:'Faculty master dataset is unavailable; cannot identify the faculty member.'};
 const hits=list.filter(x=>norm(x.name)===norm(v));
 if(hits.length===1)return{f:hits[0]};
 if(hits.length>1)return{err:'Several faculty share this name. Please contact the administrator.'};
 return{err:'No faculty record matches. Pick a name from the suggestion list.'};
}
function onName(){
 const r=resolveFaculty();state.facId=r.f?r.f.id:null;
 if(r.f){$('match').textContent='Matched faculty ID: '+r.f.id;$('name').value=r.f.name;}
 else $('match').textContent=$('name').value?'Not matched to a faculty record':'';
 state.result=null;save();
}
function autofill(){
 const e=validYears($('y1').value.trim(),$('y2').value.trim());$('yErr').textContent=e;if(e){say('Fix the appraisal year first.','danger');return;}
 const r=resolveFaculty();if(r.err){say(esc(r.err),'danger');return;}
 state.facId=r.f.id;
 const miss=['attendance','certificates'].filter(k=>!DATA[k]);
 if(!DATA.attendance){say('Attendance dataset is unavailable ('+esc(DATA.errors.attendance||'not loaded')+'). Points 16/17 were NOT calculated — this is a data failure, not a zero result.','danger');renderReport(null,r.f);return;}
 const res=compute(r.f,DATA,+$('y1').value);state.result=res;
 $('p16').value=res.p16;$('p17').value=res.p17;
 let m='Calculation succeeded for <b>'+esc(r.f.name)+'</b>: Point 16 = '+res.p16+', Point 17 = '+res.p17+'.';
 if(!res.rows.length)m+=' No event records were found for this faculty (genuine zero, datasets loaded).';
 if(res.flagged)m+=' <b>'+res.flagged+'</b> event(s) flagged for review (Pending Classification).';
 if(!res.periodApplied)m+=' No appraisal-period rule is configured, so events were not filtered by date.';
 if(res.dupEvents||res.dupCerts)m+=' Duplicates ignored: '+res.dupEvents+' event record(s), '+res.dupCerts+' certificate(s).';
 if(miss.includes('certificates'))m+=' Certificate dataset unavailable: verification statistics not shown.';
 say(m,res.flagged||miss.length?'warning':'success');
 renderReport(res,r.f);save();
}
function renderReport(res,f){
 const y=$('y1').value&&$('y2').value?$('y1').value+'-'+$('y2').value:'not entered';
 let h='<table class="mb-2"><tr><th>Faculty name</th><td>'+esc(f.name)+'</td><th>Department</th><td>'+esc($('dept').value||'Unavailable')+'</td><th>Appraisal year</th><td>'+esc(y)+'</td></tr></table>';
 if(!res){$('repBody').innerHTML=h+'<div class="bad">Report unavailable: required dataset could not be retrieved.</div>';return;}
 const n=DATA.certificates?null:'Unavailable',s=res.stats;
 h+='<table class="mb-2"><tr><th>Total Certificates Submitted</th><th>Valid</th><th>Invalid</th><th>Pending Review</th></tr><tr>'
  +[s.total,s.valid,s.invalid,s.pending].map(v=>'<td>'+(n||v)+'</td>').join('')+'</tr></table>';
 if(!res.rows.length)h+='<div>No event or certificate records found for this faculty member.</div>';
 else h+='<div class="rt"><table><thead><tr><th>Sl. No.</th><th>Certificate/Event Name</th><th>Institution or Event Venue</th><th>Event Date or Date Range</th><th>Event Classification</th><th>Certificate Status</th><th>Verification Reason</th><th>Contribution to Appraisal</th></tr></thead><tbody>'
  +res.rows.map((r,i)=>'<tr><td>'+(i+1)+'</td><td>'+esc(r.name)+'</td><td>'+esc(r.venue||'Not available')+'</td><td>'+esc(r.dates||'Not available')+'</td><td>'+(r.cls==='Unknown'?'Unknown (review)':r.cls)+'</td><td>'+(r.st||'No certificate submitted')+'</td><td>'+esc(r.reason||'—')+'</td><td>'+r.contrib+(r.why?'<br><small>'+esc(r.why)+'</small>':'')+'</td></tr>').join('')+'</tbody></table></div>';
 h+='<p class="small mt-2">Points 16/17 reflect all certificates/events classified by venue (Internal/External); certificate validity does not affect the count.</p>';
 $('repBody').innerHTML=h;
}
function calc(){
 for(const id of['p16','p17']){if($(id).value!==''&&!validCount($(id).value)){say('Points 16 and 17 must be non-negative whole numbers.','danger');return;}}
 const r=scoreCalc(+$('p16').value||0,+$('p17').value||0);
 if(!r){['tot','bon','fin'].forEach(i=>$(i).value='');$('scoreMsg').textContent='Score calculation requires configuration: official scoring weights/maximums have not been provided (CONFIG.scoring).';save();return;}
 $('tot').value=r.total;$('bon').value=r.bonus;$('fin').value=r.final;$('scoreMsg').textContent='';save();
}
function save(){try{localStorage.setItem(LS_KEY,JSON.stringify({y1:$('y1').value,y2:$('y2').value,name:$('name').value,dept:$('dept').value,desig:$('desig').value,p16:$('p16').value,p17:$('p17').value,tot:$('tot').value,bon:$('bon').value,fin:$('fin').value}));}catch(e){}}
function restore(){try{const d=JSON.parse(localStorage.getItem(LS_KEY)||'null');if(!d||typeof d!=='object')return;
 if(/^\\d{4}$/.test(d.y1||''))$('y1').value=d.y1;if(/^\\d{4}$/.test(d.y2||''))$('y2').value=d.y2;
 if(typeof d.name==='string')$('name').value=d.name.slice(0,120);if(typeof d.dept==='string')$('dept').value=d.dept.slice(0,120);
 if(['Assistant Professor','Associate Professor','Professor'].includes(d.desig))$('desig').value=d.desig;
 if(validCount(d.p16||'x'))$('p16').value=d.p16;if(validCount(d.p17||'x'))$('p17').value=d.p17;
 for(const k of['tot','bon','fin'])if(/^\\d+(\\.\\d+)?$/.test(d[k]||''))$(k).value=d[k];
 say('Saved form entries restored. Run “Autofill Appraisal Details” to regenerate the verification report.','info');}catch(e){}}
function reset(){
 if(!confirm('Clear the appraisal form and calculated results? Project datasets are not affected.'))return;
 ['y1','y2','name','dept','p16','p17','tot','bon','fin'].forEach(i=>$(i).value='');$('desig').selectedIndex=0;
 $('match').textContent='';$('yErr').textContent='';$('scoreMsg').textContent='';$('msg').innerHTML='';
 state={facId:null,result:null};$('repBody').textContent='Select a faculty member and click “Autofill Appraisal Details”.';
 try{localStorage.removeItem(LS_KEY);}catch(e){}
}
['p16','p17'].forEach(id=>$(id).addEventListener('input',()=>{const v=$(id).value;
 if(v!==''&&!validCount(v)){$(id).classList.add('is-invalid');}else $(id).classList.remove('is-invalid');save();}));
['y1','y2','dept','desig'].forEach(id=>$(id).addEventListener('change',save));
$('name').addEventListener('change',onName);
$('bAuto').onclick=autofill;$('bCalc').onclick=calc;$('bReset').onclick=reset;
$('bPrint').onclick=()=>{
 if(!state.result)say('No verification report generated yet; the printout will omit report details. Click Autofill first for a complete printout.','warning');
 calc();window.print();};

restore();loadData();
}
</script></body></html>"""

html_out = TEMPLATE.replace("__FAC_JSON__", fac_json).replace("__ATT_JSON__", att_json).replace("__CERT_JSON__", cert_json)

out_path = os.path.join(base_dir, "appraisal_form.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html_out)

print(f"Successfully generated {out_path} ({len(html_out)} bytes)")
