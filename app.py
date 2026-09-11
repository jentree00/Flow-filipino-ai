import os, uuid, time, threading, json, subprocess, shlex
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
import requests

ROOT=Path(__file__).parent
UPLOADS=ROOT/'uploads'; OUTPUTS=ROOT/'outputs'
UPLOADS.mkdir(exist_ok=True); OUTPUTS.mkdir(exist_ok=True)
JOBS={}
COMFY=os.getenv('COMFYUI_URL','http://127.0.0.1:8188')
WORKFLOW=ROOT/'workflow_api.json'
app=Flask(__name__)

@app.get('/')
def home(): return send_from_directory(ROOT,'index.html')
@app.get('/<path:p>')
def static(p): return send_from_directory(ROOT,p)

@app.get('/api/health')
def health():
    try:
        r=requests.get(COMFY+'/system_stats',timeout=2)
        return jsonify(comfyui=r.ok,url=COMFY,ffmpeg=bool(shutil_which('ffmpeg')))
    except Exception:
        return jsonify(comfyui=False,url=COMFY,ffmpeg=bool(shutil_which('ffmpeg')))

def shutil_which(name):
    import shutil
    return shutil.which(name)

def output_url(h):
    for node in h.get('outputs',{}).values():
        for typ in ('videos','gifs','images'):
            for x in node.get(typ,[]) or []:
                if x.get('filename'):
                    q=requests.compat.urlencode({'filename':x['filename'],'subfolder':x.get('subfolder',''),'type':x.get('type','output')})
                    return COMFY+'/view?'+q, x
    return None, None

def comfy_upload(local_path):
    with open(local_path,'rb') as fh:
        r=requests.post(COMFY+'/upload/image',files={'image':(local_path.name,fh,'image/png')},data={'type':'input','overwrite':'true'},timeout=60)
    r.raise_for_status(); data=r.json(); return data.get('name') or local_path.name

def download_comfy_video(url, dest):
    r=requests.get(url,timeout=120,stream=True); r.raise_for_status()
    with open(dest,'wb') as f:
        for chunk in r.iter_content(1024*1024):
            if chunk: f.write(chunk)

def ffmpeg_upscale(src, dest, width, height):
    ff=shutil_which('ffmpeg')
    if not ff: return False, 'FFmpeg not installed'
    cmd=[ff,'-y','-i',str(src),'-vf',f'scale={width}:{height}:flags=lanczos','-c:v','libx264','-preset','medium','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if p.returncode!=0: return False,p.stderr[-1800:]
    return True,None

def worker(j,pid,quality,fmt):
    for _ in range(900):
        try:
            h=requests.get(f'{COMFY}/history/{pid}',timeout=5).json().get(pid)
            if h:
                status=h.get('status',{})
                if status.get('status_str')=='error':
                    JOBS[j]|={'status':'error','error':'ComfyUI workflow error'}; return
                u,meta=output_url(h)
                if u:
                    raw=OUTPUTS/f'{j}_raw.webm'
                    download_comfy_video(u,raw)
                    targets={'9:16':(720,1280),'16:9':(1280,720),'1:1':(720,720)}
                    w,hgt=targets.get(fmt,(720,1280))
                    final=OUTPUTS/f'{j}_{quality.replace("p","")}_{w}x{hgt}.mp4'
                    if quality=='1080p':
                        # Wan 2.1 I2V natively supports 720p; 1080p here is high-quality Lanczos post-upscale.
                        if fmt=='9:16': w,hgt=1080,1920
                        elif fmt=='16:9': w,hgt=1920,1080
                        else: w,hgt=1080,1080
                        final=OUTPUTS/f'{j}_1080p_{w}x{hgt}.mp4'
                    ok,err=ffmpeg_upscale(raw,final,w,hgt)
                    if not ok:
                        final=raw
                    JOBS[j]|={'status':'done','progress':100,'video':f'/media/{final.name}','quality':quality,'upscaled':quality=='1080p' and ok}
                    return
        except Exception as e:
            JOBS[j]['last_error']=str(e)
        JOBS[j]['progress']=min(95,JOBS[j].get('progress',1)+1)
        time.sleep(2)
    JOBS[j]|={'status':'error','error':'Timed out waiting for ComfyUI'}

@app.post('/api/generate')
def generate():
    f=request.files.get('image')
    if not f: return jsonify(error='Image is required'),400
    j=str(uuid.uuid4()); p=UPLOADS/(j+(Path(f.filename or '.png').suffix or '.png')); f.save(p)
    try:
        comfy_name=comfy_upload(p); wf=json.loads(WORKFLOW.read_text())
        wf['52']['inputs']['image']=comfy_name
        wf['6']['inputs']['text']=request.form.get('prompt','')
        fmt=request.form.get('format','9:16')
        if fmt=='16:9': wf['50']['inputs']['width']=1280; wf['50']['inputs']['height']=720
        elif fmt=='1:1': wf['50']['inputs']['width']=720; wf['50']['inputs']['height']=720
        else: wf['50']['inputs']['width']=720; wf['50']['inputs']['height']=1280
        duration=int(request.form.get('duration','5'))
        wf['50']['inputs']['length']=max(17,min(81,duration*8+1))
        r=requests.post(COMFY+'/prompt',json={'prompt':wf},timeout=30); r.raise_for_status()
        pid=r.json().get('prompt_id')
        if not pid: return jsonify(error='ComfyUI did not return prompt_id'),502
        quality=request.form.get('quality','720p')
        JOBS[j]={'status':'queued','progress':1,'prompt_id':pid,'quality':quality}
        threading.Thread(target=worker,args=(j,pid,quality,fmt),daemon=True).start()
        return jsonify(job_id=j)
    except Exception as e: return jsonify(error=str(e)),502

@app.get('/api/job/<j>')
def job(j): return jsonify(JOBS.get(j,{'status':'unknown'}))

@app.get('/media/<path:name>')
def media(name): return send_from_directory(OUTPUTS,name,as_attachment=False)

@app.post('/api/edit')
def edit_video():
    ff=shutil_which('ffmpeg')
    if not ff: return jsonify(error='FFmpeg is required for video editing. Run the one-click installer first.'),503
    video=request.files.get('video')
    if not video: return jsonify(error='Video is required'),400
    j=str(uuid.uuid4()); src=UPLOADS/f'edit_{j}{Path(video.filename or ".mp4").suffix or ".mp4"}'; video.save(src)
    audio=request.files.get('audio'); audio_path=None
    if audio and audio.filename:
        audio_path=UPLOADS/f'audio_{j}{Path(audio.filename).suffix or ".wav"}'; audio.save(audio_path)
    start=max(0,float(request.form.get('start','0') or 0)); end=float(request.form.get('end','0') or 0)
    dialogue=(request.form.get('dialogue','') or '').strip()
    burn_subtitles=request.form.get('burn_subtitles','1') == '1'
    replace_audio_only=request.form.get('replace_audio_only','0') == '1'
    # Simple SRT with one corrected dialogue line spanning the selected segment.
    srt=None
    if dialogue and burn_subtitles and not replace_audio_only:
        srt=UPLOADS/f'{j}.srt'
        dur=max(1,end-start) if end>start else 9999
        def ts(sec):
            ms=int((sec-int(sec))*1000); sec=int(sec); return f'{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d},{ms:03d}'
        srt.write_text(f'1\n{ts(0)} --> {ts(dur)}\n{dialogue}\n',encoding='utf-8')
    out=OUTPUTS/f'edited_{j}.mp4'
    cmd=[ff,'-y']
    if start>0: cmd += ['-ss',str(start)]
    cmd += ['-i',str(src)]
    if audio_path: cmd += ['-i',str(audio_path)]
    vf=[]
    if srt: vf.append("subtitles='"+str(srt).replace('\\','/')+"'")
    if vf: cmd += ['-vf',','.join(vf)]
    if end>start: cmd += ['-t',str(end-start)]
    if audio_path: cmd += ['-map','0:v:0','-map','1:a:0','-shortest','-c:a','aac','-b:a','192k']
    else: cmd += ['-c:a','aac','-b:a','192k']
    cmd += ['-c:v','libx264','-preset','medium','-crf','18','-movflags','+faststart',str(out)]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if p.returncode!=0: return jsonify(error=p.stderr[-2500:]),500
    return jsonify(video=f'/media/{out.name}')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','3000')),debug=False)

# --- Multi-engine cloud adapters -------------------------------------------------
def _data_url_parts(data_url):
    if not data_url or ',' not in data_url: return None,None
    head, payload=data_url.split(',',1)
    mime=(head.split(';')[0].split(':',1)[1] if head.startswith('data:') else 'image/jpeg')
    return mime,payload

def _extract_omni_video(resp):
    # REST puts video bytes inside steps[].model_output.content[].
    for step in resp.get('steps',[]) or []:
        for c in step.get('content',[]) or []:
            if c.get('type')=='video' and c.get('data'):
                return c['data']
    return None

@app.post('/api/generate/omni')
def generate_omni():
    """Gemini Omni 1.1 Flash text/image-to-video adapter."""
    data=request.get_json(silent=True) or {}
    key=data.get('api_key') or os.getenv('GEMINI_API_KEY')
    if not key: return jsonify(error='Gemini API key is required for Omni.'),400
    prompt=data.get('prompt','').strip()
    if not prompt: return jsonify(error='Prompt is required'),400
    rf={'type':'video','aspect_ratio':data.get('aspect_ratio','16:9'),'resolution':data.get('resolution','720p')}
    inputs=[]
    if data.get('image_data'):
        mime,b64=_data_url_parts(data['image_data'])
        if b64: inputs.append({'type':'image','data':b64,'mime_type':mime or 'image/jpeg'})
    inputs.append({'type':'text','text':prompt}) if inputs else None
    payload={'model':'gemini-omni-1.1-flash','input':inputs if inputs else prompt,'response_format':rf}
    r=requests.post('https://generativelanguage.googleapis.com/v1beta/interactions',params={'key':key},json=payload,timeout=900)
    if not r.ok: return jsonify(error=r.text[:3000]),r.status_code
    video_b64=_extract_omni_video(r.json())
    if not video_b64: return jsonify(error='Omni completed without a video output.'),502
    j=str(uuid.uuid4()); out=OUTPUTS/f'omni_{j}.mp4'
    import base64
    out.write_bytes(base64.b64decode(video_b64))
    return jsonify(video=f'/media/{out.name}',engine='Gemini Omni 1.1 Flash',resolution=rf['resolution'])

@app.post('/api/generate/veo')
def generate_veo():
    """Veo 3.1 Vertex AI adapter. Uses GOOGLE_ACCESS_TOKEN or gcloud auth on the host."""
    data=request.get_json(silent=True) or {}
    project=data.get('project_id') or os.getenv('GOOGLE_CLOUD_PROJECT')
    model=data.get('model') or 'veo-3.1-generate-001'
    token=os.getenv('GOOGLE_ACCESS_TOKEN')
    if not token:
        try: token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True,timeout=15).strip()
        except Exception: token=''
    if not project: return jsonify(error='Google Cloud Project ID is required for Veo.'),400
    if not token: return jsonify(error='Google access token not found. Run gcloud auth login or set GOOGLE_ACCESS_TOKEN.'),400
    prompt=data.get('prompt','').strip()
    if not prompt: return jsonify(error='Prompt is required'),400
    location=os.getenv('GOOGLE_CLOUD_LOCATION','us-central1')
    instance={'prompt':prompt}
    if data.get('image_data'):
        mime,b64=_data_url_parts(data['image_data'])
        if b64: instance['image']={'bytesBase64Encoded':b64,'mimeType':mime or 'image/jpeg'}
    params={'aspectRatio':data.get('aspect_ratio','16:9'),'resolution':data.get('resolution','720p'),'sampleCount':1}
    storage=os.getenv('VEO_OUTPUT_STORAGE_URI')
    if storage: params['storageUri']=storage
    url=f'https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:predictLongRunning'
    r=requests.post(url,headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json={'instances':[instance],'parameters':params},timeout=60)
    if not r.ok:return jsonify(error=r.text[:3000]),r.status_code
    op=r.json().get('name')
    return jsonify(operation=op,message='Veo job submitted. Configure VEO_OUTPUT_STORAGE_URI for automatic cloud output retrieval.',engine=model)
