import anthropic, os, json, requests, time, subprocess, re
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_API_KEY","")
KIE_KEY        = os.environ.get("KIE_API_KEY","")
EL_KEY         = os.environ.get("ELEVENLABS_API_KEY","")
VOICE_ID       = "JbND05fzfuuytlmRyQ4J"
BASE_URL       = "https://api.kie.ai"
client         = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
DIAS           = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"]
HORARIOS_SLOT  = {"manana":"07:00","tarde":"14:00","noche":"20:00"}

UNIVERSOS = {
"suegra_clasemedia":{"desc":"Suegra clasemedia presuntuosa que odia a la nuera","visual":"dramatic mexican middle class woman pretentious living room intense argument younger woman telenovela photorealistic 4k portrait vertical"},
"suegra_barrio":{"desc":"Suegra mandona metiche controla todo usa enfermedad ficticia para manipular","visual":"older loud mexican woman colorful working class home screaming argument younger woman neighbors watching dramatic photorealistic 4k portrait vertical"},
"familia_mantenida":{"desc":"Familia entera vive del sueldo de quien trabaja nadie mas aporta","visual":"exhausted young woman arriving home lazy family watching TV eating modest apartment dramatic photorealistic 4k portrait vertical"},
"cliente_fifi":{"desc":"Clienta clasista humilla a trabajadora de servicio y la menosprecia","visual":"overdressed pretentious woman extremely rude humble service worker dramatic confrontation beauty salon photorealistic 4k portrait vertical"},
"vecina_metiche":{"desc":"Vecina graba todo sabe secretos de todos pero tiene su propio escandalo","visual":"nosy neighbor recording phone from window apartment building neighbors watching dramatic expression photorealistic 4k portrait vertical"},
"amiga_vibora":{"desc":"Mejor amiga que conto todos los secretos intento quitarle a su pareja","visual":"two women intense confrontation betrayal one crying angry other fake smiling living room dramatic photorealistic 4k portrait vertical"},
"nina_rica_novio_pobre":{"desc":"Ella tiene mas recursos se enamoro de alguien de menos posibilidades familia la presiona","visual":"young elegant woman humble boyfriend rich family dinner disapproving wealthy parents staring class contrast dramatic photorealistic 4k portrait vertical"},
"nuera_explota":{"desc":"Nuera que aguanto anos de maltrato el dia que exploto dijo todo lo que sabia","visual":"young woman confronting entire in-law family dinner table dramatic explosion emotions shocked family faces photorealistic 4k portrait vertical"},
"trabajo_toxico":{"desc":"Trabajo toxico jefa con favoritas alguien robo credito de proyecto afectada tiene pruebas pero miedo","visual":"dramatic office women confrontation cubicles tense atmosphere gossip betrayal expressions photorealistic 4k portrait vertical"},
"famoso":{"desc":"Famoso o famosa sin nombre solo pistas especificas que todos adivinen","visual":"mysterious blurred silhouette celebrity glamorous event paparazzi dramatic lighting luxury gossip magazine 4k portrait vertical"},
}

def get_carpeta_semana():
    hoy = datetime.now()
    lunes = hoy - timedelta(days=hoy.weekday())
    base = "output/Semana_" + lunes.strftime("%Y-%m-%d")
    for sub in ["imagenes","audios","videos","publicaciones"]:
        os.makedirs(base+"/"+sub, exist_ok=True)
    return base

def get_numero(base):
    existentes = os.listdir(base+"/publicaciones") if os.path.exists(base+"/publicaciones") else []
    return len([f for f in existentes if f.endswith(".json")]) + 1

def generar_drama(universo_key):
    u = UNIVERSOS[universo_key]
    prompt = "\n".join([
        "Eres el escritor de chismes mas picoso de Mexico para Le Chisme.",
        "PRIMERA PERSONA como si la protagonista misma lo narra en audio.",
        "CERO nombres propios. Solo: mi esposo, mi suegra, mi cunada, mi jefa, la vecina.",
        "CERO lugares especificos. Solo: el hospital, la oficina, el super, el fraccionamiento.",
        "El texto del AUDIO debe durar exactamente 45-55 segundos al leerlo en voz alta (unas 120-140 palabras).",
        "Que de coraje escucharlo. Primera persona directa con gancho desde la primera oracion.",
        "CONTEXTO: "+universo_key,
        "DESC: "+u["desc"],
        "",
        "ESTRUCTURA del audio (120-140 palabras total):",
        "- Oracion 1: El gancho que engancha inmediatamente",
        "- Parrafo 2-3: El drama con detalles especificos",
        "- Parrafo 4: El momento que todo explota",
        "- Ultima oracion: Giro sin conclusion que obliga a comentar",
        "",
        "Lenguaje mexicano real. Sin nombres ni lugares especificos.",
        "Si es famoso NUNCA el nombre solo pistas especificas.",
        "",
        "Responde SOLO este JSON sin backticks ni saltos de linea dentro de los valores:",
        '{"titulo":"TITULAR MAYUSCULAS max 8 palabras","audio_texto":"el texto completo para narrar en voz alta 120-140 palabras sin saltos de linea","pregunta_polemica":"pregunta corta que divida en dos bandos","caption_tiktok":"caption viral emojis max 200 chars","hashtags":"#lechisme #chisme #dramareal #mexico #viral #parati #fyp #chismemexicano #telenovela #comentalo"}',
    ])
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=1500, messages=[{"role":"user","content":prompt}])
    texto = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
    s = texto.find("{")
    e = texto.rfind("}")
    if s >= 0 and e > s:
        candidate = texto[s:e+1]
        try:
            return json.loads(candidate)
        except:
            cleaned = candidate.replace("\n"," ").replace("\r","")
            try:
                return json.loads(cleaned)
            except:
                cleaned2 = re.sub(r'"([^"]*)"(\s*[^:,}\]])', lambda m: '"'+m.group(1).replace('"',"'")+'"'+m.group(2), cleaned)
                return json.loads(cleaned2)
    raise ValueError("No JSON")

def generar_voz(texto, path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": EL_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": texto,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.6,
            "use_speaker_boost": True
        }
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    if r.status_code == 200:
        open(path,"wb").write(r.content)
        print("  Audio generado: "+path)
        return path
    print("  Error voz: "+r.text[:100])
    return None

def generar_imagen(prompt_visual, nombre, base):
    headers = {"Authorization":"Bearer "+KIE_KEY,"Content-Type":"application/json"}
    payload = {"model":"bytedance/seedream-v4-text-to-image","input":{"prompt":prompt_visual,"image_size":"portrait_16_9","image_resolution":"1K","max_images":1}}
    r = requests.post(BASE_URL+"/api/v1/jobs/createTask",headers=headers,json=payload,timeout=60)
    if r.status_code!=200 or r.json().get("code")!=200:
        print("  Error imagen: "+r.text[:100])
        return None
    task_id = r.json()["data"]["taskId"]
    print("  Task imagen: "+task_id)
    for i in range(60):
        time.sleep(5)
        r2 = requests.get(BASE_URL+"/api/v1/jobs/recordInfo?taskId="+task_id,headers=headers,timeout=15)
        if r2.status_code==200:
            d = r2.json().get("data",{})
            state = d.get("state","")
            print("  "+state+" ("+str(i*5)+"s)")
            if state=="success":
                rj = json.loads(d.get("resultJson","{}"))
                url = rj.get("resultUrls",[""])[0]
                if url:
                    img_data = requests.get(url,timeout=60).content
                    path = base+"/imagenes/"+nombre+".jpg"
                    open(path,"wb").write(img_data)
                    return path
            elif state in ["failed","fail","error"]:
                return None
    return None

def agregar_logo(img_path):
    img = Image.open(img_path).convert("RGBA")
    w,h = img.size
    ov = Image.new("RGBA",(w,h),(0,0,0,0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0,0,w,130],fill=(0,0,0,200))
    img = Image.alpha_composite(img,ov).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        fl = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",42)
        fs = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",27)
    except:
        fl=fs=ImageFont.load_default()
    draw.text((w//2,48),"LE CHISME",fill="#C9A84C",font=fl,anchor="mm")
    draw.text((w//2,95),"@lechisme.oficial",fill="#aaaaaa",font=fs,anchor="mm")
    out = img_path.replace(".jpg","_logo.jpg")
    img.save(out,quality=95)
    return out

def crear_video_con_voz(img_path, audio_path, texto_audio, nombre, base):
    out = base+"/videos/"+nombre+".mp4"
    
    # Paso 1: Video con imagen y audio
    cmd1 = [
        "ffmpeg","-y",
        "-loop","1","-i",img_path,
        "-i",audio_path,
        "-c:v","libx264","-tune","stillimage",
        "-c:a","aac","-b:a","192k",
        "-pix_fmt","yuv420p",
        "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-shortest",
        base+"/videos/"+nombre+"_temp.mp4"
    ]
    res1 = subprocess.run(cmd1, capture_output=True)
    if res1.returncode != 0:
        print("  Error video: "+res1.stderr.decode()[:100])
        return None

    # Paso 2: Agregar subtitulos con drawtext
    palabras = texto_audio.split()
    chunk_size = 6
    chunks = [" ".join(palabras[i:i+chunk_size]) for i in range(0, len(palabras), chunk_size)]
    
    dur_total = len(palabras) / 2.8  # ~2.8 palabras por segundo
    dur_chunk = dur_total / len(chunks)
    
    filtros = []
    for idx, chunk in enumerate(chunks):
        t_start = idx * dur_chunk
        t_end = t_start + dur_chunk
        chunk_escaped = chunk.replace("'", "\\'").replace(":", "\\:")
        filtros.append(
            f"drawtext=text='{chunk_escaped}':fontsize=44:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-200:enable='between(t,{t_start:.1f},{t_end:.1f})'"
        )
    
    filtro_str = ",".join(filtros)
    
    cmd2 = [
        "ffmpeg","-y",
        "-i",base+"/videos/"+nombre+"_temp.mp4",
        "-vf",filtro_str,
        "-c:a","copy",
        out
    ]
    res2 = subprocess.run(cmd2, capture_output=True)
    
    # Limpiar temp
    try:
        os.remove(base+"/videos/"+nombre+"_temp.mp4")
    except:
        pass
    
    if res2.returncode == 0:
        print("  Video con subtitulos: "+out)
        return out
    else:
        print("  Error subtitulos, usando video simple")
        return base+"/videos/"+nombre+"_temp.mp4" if os.path.exists(base+"/videos/"+nombre+"_temp.mp4") else None

def publicar(universo_key, slot="manana"):
    base = get_carpeta_semana()
    numero = get_numero(base)
    dia_nombre = DIAS[datetime.now().weekday()]
    hora = HORARIOS_SLOT.get(slot,"00:00")
    prefijo = str(numero).zfill(2)+"_"+dia_nombre+"_"+hora.replace(":","h")
    
    print("\nEP #"+str(numero)+" | "+dia_nombre+" "+hora+" | "+universo_key)
    print("Generando drama...")
    drama = generar_drama(universo_key)
    titulo = drama.get("titulo","")
    audio_texto = drama.get("audio_texto","")
    
    print("Titulo: "+titulo)
    print("Audio ("+str(len(audio_texto.split()))+" palabras):")
    print(audio_texto)
    print("\nPREGUNTA: "+drama.get("pregunta_polemica",""))
    print("\nTIKTOK: "+drama.get("caption_tiktok",""))
    print("\nHASHTAGS: "+drama.get("hashtags",""))
    
    slug = "".join(c for c in titulo.lower()[:25].replace(" ","_") if c.isalnum() or c=="_")
    nombre_final = prefijo+"_"+slug
    
    print("\nGenerando voz...")
    audio = generar_voz(audio_texto, base+"/audios/"+nombre_final+".mp3")
    
    print("Generando imagen...")
    img = generar_imagen(UNIVERSOS[universo_key]["visual"], nombre_final+"_raw", base)
    
    video = None
    if img and audio:
        img_logo = agregar_logo(img)
        img_path = base+"/imagenes/"+nombre_final+".jpg"
        os.rename(img_logo, img_path)
        print("Creando video con voz y subtitulos...")
        video = crear_video_con_voz(img_path, audio, audio_texto, nombre_final, base)
    
    pub = {
        "numero":numero,"dia":dia_nombre,"hora":hora,
        "titulo":titulo,"audio_texto":audio_texto,
        "pregunta":drama.get("pregunta_polemica",""),
        "caption_tiktok":drama.get("caption_tiktok",""),
        "hashtags":drama.get("hashtags",""),
        "imagen":base+"/imagenes/"+nombre_final+".jpg",
        "audio":audio,"video":video
    }
    
    open(base+"/publicaciones/"+nombre_final+".json","w",encoding="utf-8").write(
        json.dumps(pub,ensure_ascii=False,indent=2))
    
    print("\nARCHIVOS EN: "+base)
    if video and os.path.exists(video):
        subprocess.run(["open",video])
    subprocess.run(["open",base])
    return pub

def generar_dia():
    import random
    dia = datetime.now().weekday()
    regulares = [k for k in UNIVERSOS if k!="famoso"]
    es_famoso = dia in [0,2,4,6]
    for universo,slot in [
        (random.choice(regulares),"manana"),
        (random.choice(regulares),"tarde"),
        ("famoso" if es_famoso else random.choice(regulares),"noche")
    ]:
        publicar(universo,slot)
        time.sleep(3)

import sys
if len(sys.argv)>1:
    if sys.argv[1]=="dia":
        generar_dia()
    elif sys.argv[1] in UNIVERSOS:
        publicar(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else "manana")
    else:
        print("Universos: "+" | ".join(UNIVERSOS.keys()))
else:
    publicar("suegra_clasemedia")
