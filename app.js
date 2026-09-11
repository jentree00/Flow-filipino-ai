const $=s=>document.querySelector(s);let characters=JSON.parse(localStorage.getItem("ffai_characters")||"[]"),scenes=[];
function preview(input,target){input.onchange=()=>{let f=input.files[0];if(f)target.innerHTML=`<img src="${URL.createObjectURL(f)}">`}}preview($("#charImage"),$("#charPreview"));
function renderChars(){$("#characters").innerHTML=characters.map((c,i)=>`<span class="chip">${esc(c.name)} · ${esc(c.role)} <button onclick="useChar(${i})">Use</button></span>`).join("")}window.useChar=i=>{$("#charName").value=characters[i].name};renderChars();
$("#charImage").onchange=()=>$("#charFile").textContent=$("#charImage").files[0]?.name||"PNG/JPG/WebP";
$("#saveCharacter").onclick=()=>{let f=$("#charImage").files[0],n=$("#charName").value.trim();if(!f||!n)return alert("Add character name and image.");let r=new FileReader();r.onload=()=>{characters.push({name:n,role:$("#charRole").value,image:r.result});localStorage.setItem("ffai_characters",JSON.stringify(characters));renderChars()};r.readAsDataURL(f)};
$("#makeStoryboard").onclick=()=>{let t=$("#story").value.trim();if(!t)return alert("Paste a story first.");let n=Math.max(1,Math.min(20,+$("#sceneCount").value||6)),a=t.split(/(?<=[.!?])\s+/).filter(Boolean);scenes=Array.from({length:n},(_,i)=>({id:i+1,title:`Scene ${String(i+1).padStart(2,"0")}`,description:a[i%Math.max(1,a.length)]||t,prompt:`${$("#genre").value}, cinematic Filipino scene, ${a[i%Math.max(1,a.length)]||t}, natural acting, realistic lighting, consistent character`,image:null}));renderScenes()};
function renderScenes(){$("#storyboard").innerHTML=scenes.map(s=>`<div class="scene"><h3>${s.title}</h3><p>${esc(s.description)}</p><input type="file" accept="image/*" data-img="${s.id}"><textarea rows="4" data-prompt="${s.id}">${esc(s.prompt)}</textarea><button onclick="saveScene(${s.id})">Save</button></div>`).join("")}
window.saveScene=id=>{let s=scenes.find(x=>x.id===id),ta=document.querySelector(`[data-prompt="${id}"]`),inp=document.querySelector(`[data-img="${id}"]`);s.prompt=ta.value;if(inp.files[0]){let r=new FileReader();r.onload=()=>{s.image=r.result;alert(`Scene ${id} saved.`)};r.readAsDataURL(inp.files[0])}else alert(`Scene ${id} saved.`)};
function esc(x){return String(x).replace(/[&<>\"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","\\":"&#92;"}[m]))}
async function health(){try{let d=await (await fetch("/api/health")).json();$("#health").textContent=d.comfyui?`● AI online • ${d.ffmpeg?'FFmpeg ready':'FFmpeg missing'}`:`○ UI online • connect ComfyUI`}catch{$("#health").textContent="○ UI online"}}health();setInterval(health,5000);
$("#generateAll").onclick=async()=>{if(!scenes.length)return alert("Generate a storyboard first.");$("#jobs").innerHTML="";for(let s of scenes){let c=document.createElement("div");c.className="job";c.innerHTML=`<strong>${s.title}</strong><span class="small">Starting…</span><div class="bar"><i></i></div>`;$("#jobs").append(c);if(!s.image){c.querySelector(".small").textContent="Skipped — add an image";continue}try{let b=await (await fetch(s.image)).blob(),fd=new FormData();fd.append("image",b,`scene-${s.id}.png`);fd.append("prompt",s.prompt);fd.append("duration",$("#duration").value);fd.append("format",$("#format").value);fd.append("quality",$("#quality").value);let r=await fetch("/api/generate",{method:"POST",body:fd}),d=await r.json();if(!r.ok)throw Error(d.error||"Generation failed");await poll(d.job_id,c)}catch(e){c.querySelector(".small").textContent=e.message}}};
async function poll(id,c){for(let i=0;i<600;i++){await new Promise(r=>setTimeout(r,2000));let d=await (await fetch(`/api/job/${id}`)).json();c.querySelector("i").style.width=(d.progress||Math.min(95,5+i/5))+"%";c.querySelector(".small").textContent=d.status||"Generating…";if(d.status==="done"){c.querySelector(".small").textContent=`Done • ${d.quality}${d.upscaled?' • upscaled':''}`;c.insertAdjacentHTML("beforeend",`<video controls src="${d.video}"></video><button onclick="openEditor('${d.video}')">Edit Dialogue</button>`);return}if(d.status==="error"){c.querySelector(".small").textContent=d.error||"Error";return}}}
window.openEditor=url=>{document.querySelector('.editor').scrollIntoView({behavior:'smooth'});let v=$("#editPreview");v.src=url;window._editorSource=url;};
$("#editVideo").onchange=()=>{let f=$("#editVideo").files[0];if(f){$("#editPreview").src=URL.createObjectURL(f);window._editorSource=null}};
$("#editExport").onclick=async()=>{let file=$("#editVideo").files[0],fd=new FormData();if(file)fd.append('video',file,file.name);else if(window._editorSource){let b=await (await fetch(window._editorSource)).blob();fd.append('video',b,'generated.mp4')}else return alert('Pumili muna ng video.');let a=$("#editAudio").files[0];if(a)fd.append('audio',a,a.name);fd.append('start',$("#editStart").value);fd.append('end',$("#editEnd").value);fd.append('dialogue',$("#editDialogue").value);$("#editResult").textContent='Processing…';try{let r=await fetch('/api/edit',{method:'POST',body:fd}),d=await r.json();if(!r.ok)throw Error(d.error||'Edit failed');$("#editResult").innerHTML=`<p>✅ Corrected video ready.</p><video controls src="${d.video}"></video><a class="download" href="${d.video}" download>Download corrected MP4</a>`}catch(e){$("#editResult").textContent=e.message}};

const settings=JSON.parse(localStorage.getItem('ffai_settings')||'{}');
if(settings.engine) $('#engine').value=settings.engine;
if(settings.veoModel) $('#veoModel').value=settings.veoModel;
if(settings.apiProject) $('#apiProject').value=settings.apiProject;
if(settings.omniKey) $('#omniKey').value=settings.omniKey;
if(settings.nativeAudio!==undefined) $('#nativeAudio').checked=settings.nativeAudio;
$('#saveSettings').onclick=()=>{localStorage.setItem('ffai_settings',JSON.stringify({engine:$('#engine').value,veoModel:$('#veoModel').value,apiProject:$('#apiProject').value,omniKey:$('#omniKey').value,nativeAudio:$('#nativeAudio').checked}));updateAdvice();alert('Engine settings saved.');};

function hasComfy(){return $('#health')?.textContent.includes('AI online')}
function pickEngine(scene){
  const manual=$('#engine').value;
  if(manual!=='auto') return manual;
  const text=(scene.prompt+' '+scene.description).toLowerCase();
  const audio=$('#nativeAudio').checked;
  const quality=$('#quality').value;
  // Veo is preferred for native audio/dialogue and final 1080p cloud shots.
  if((audio && /(dialogue|dialog|says|speak|whisper|voice|sound|music|conversation|sinabi|sabi|usap|bulong)/i.test(text)) || quality==='1080p'){
    if($('#apiProject').value.trim()) return 'veo';
  }
  if(hasComfy()) return 'wan';
  if($('#omniKey').value.trim()) return 'omni';
  if($('#apiProject').value.trim()) return 'veo';
  return 'wan';
}
function updateAdvice(){
  const e=$('#engine').value;
  $('#engineAdvice').textContent=e==='auto' ? '✨ AUTO: Wan local for no-credit production, Veo for native audio/1080p when configured, Gemini as fallback.' : `Selected engine: ${e.toUpperCase()}.`; 
}
$('#engine').addEventListener('change',updateAdvice); updateAdvice();

$('#generateAll').onclick=async()=>{
  if(!scenes.length)return alert('Generate a storyboard first.');
  const globalEngine=$('#engine').value; const cfg={engine:globalEngine,veoModel:$('#veoModel').value,apiProject:$('#apiProject').value,omniKey:$('#omniKey').value};
  $('#jobs').innerHTML='';
  for(const s of scenes){
    const engine=($('#autoPerScene').checked||globalEngine==='auto')?pickEngine(s):globalEngine;
    const c=document.createElement('div'); c.className='job'; c.innerHTML=`<strong>${esc(s.title)}</strong><span class="small">Starting ${engine.toUpperCase()}…</span><div class="bar"><i></i></div>`; $('#jobs').append(c);
    try{
      if(engine==='wan'){
        if(!s.image){c.querySelector('.small').textContent='Skipped — add an image for Wan I2V';continue;}
        let b=await (await fetch(s.image)).blob(),fd=new FormData(); fd.append('image',b,`scene-${s.id}.png`); fd.append('prompt',s.prompt); fd.append('duration',$('#duration').value); fd.append('format',$('#format').value); fd.append('quality',$('#quality').value);
        let r=await fetch('/api/generate',{method:'POST',body:fd}),d=await r.json(); if(!r.ok)throw Error(d.error||'Wan generation failed'); await poll(d.job_id,c);
      } else if(engine==='omni') {
        let body={prompt:s.prompt,aspect_ratio:$('#format').value,resolution:$('#quality').value,api_key:cfg.omniKey||undefined};
        if(s.image)body.image_data=await blobToDataURL(await (await fetch(s.image)).blob());
        let r=await fetch('/api/generate/omni',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),d=await r.json(); if(!r.ok)throw Error(d.error||'Gemini generation failed');
        c.querySelector('i').style.width='100%'; c.querySelector('.small').textContent=`Done • Gemini • ${d.resolution||$('#quality').value}`; if(d.video)c.insertAdjacentHTML('beforeend',`<video controls src="${d.video}"></video><button onclick="openEditor('${d.video}')">Edit Dialogue</button>`);
      } else {
        let body={prompt:s.prompt+(($('#nativeAudio').checked)?' Native synchronized dialogue, ambience and sound effects when appropriate.':''),aspect_ratio:$('#format').value,resolution:$('#quality').value,project_id:cfg.apiProject,model:cfg.veoModel};
        if(s.image)body.image_data=await blobToDataURL(await (await fetch(s.image)).blob());
        let r=await fetch('/api/generate/veo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),d=await r.json(); if(!r.ok)throw Error(d.error||'Veo generation failed');
        c.querySelector('.small').textContent=d.message||`Veo ${cfg.veoModel} submitted`; c.querySelector('i').style.width='100%'; if(d.video)c.insertAdjacentHTML('beforeend',`<video controls src="${d.video}"></video><button onclick="openEditor('${d.video}')">Edit Dialogue</button>`); else if(d.operation)c.insertAdjacentHTML('beforeend',`<p class="small">Operation submitted. Configure output storage to retrieve automatically.</p>`);
      }
    }catch(e){c.querySelector('.small').textContent=e.message;}
  }
};
function blobToDataURL(blob){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsDataURL(blob);});}
