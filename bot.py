import anthropic, os, json, requests, time, subprocess, re
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
KIE_KEY = os.environ.get("KIE_API_KEY","")
BASE_URL = "https://api.kie.ai"
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
DIAS = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"]
HORARIOS_SLOT = {"manana":"07:00","tarde":"14:00","noche":"20:00"}
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
    for sub in ["imagenes","videos","publicaciones"]:
        os.makedirs(base+"/"+sub, exist_ok=True)
    return base
def get_numero(base):
    existentes = os.listdir(base+"/publicaciones") if os.path.exists(base+"/publicaciones") else []
    return len([f for f in existentes if f.endswith(".json")]) + 1
def generar_drama(universo_key):
    u = UNIVERSOS[universo_key]
    prompt = "\n".join([
        "Eres el escritor de chismes mas picoso de Mexico para Le Chisme.",
        "PRIMERA PERSONA como si la protagonista misma lo escribio furiosa.",
        "CERO nombres propios. Solo: mi esposo, mi suegra, mi cunada, mi jefa, la vecina, la del trabajo.",
        "CERO lugares especificos. Solo: el hospital, la oficina, el super, el fraccionamiento, la unidad.",
        "USA: no puedo creer lo que me paso, llevo meses aguantando, me temblaron las manos.",
        "NUNCA: resulta que, me contaron, segun dicen.",
        "CONTEXTO: "+universo_key,
        "DESC: "+u["desc"],
        "",
        "5 PARRAFOS separados por doble salto de linea:",
        "1. GANCHO: quien soy que relacion tengo desde cuando. Primera persona directa.",
        "2. VENENO: que fue pasando con detalles humillaciones que aguante con coraje.",
        "3. ESCALADA: el dia que todo exploto el enfrentamiento lo que nos dijimos.",
        "4. CONSECUENCIAS: como quedo todo quien tomo partido los chismes despues.",
        "5. GIRO: algo que descubri que cambia todo. TERMINA SIN CONCLUSION.",
        "",
        "Minimo 400 palabras. Lenguaje mexicano real.",
        "Si es famoso NUNCA el nombre solo pistas que todos adivinen.",
        "",
        'Responde SOLO este JSON sin backticks:',
        '{"titulo":"TITULAR MAYUSCULAS max 8 palabras","historia_completa":"5 parrafos minimo 400 palabras","pregunta_polemica":"pregunta que divida en dos bandos","caption_tiktok":"gancho fuerte max 300 chars emojis","caption_instagram":"2 parrafos emojis pide etiquetar min 400 chars","hashtags":"#lechisme #chisme #dramareal #mexico #viral #parati #fyp #chismemexicano #suegrastoxicas #telenovela #comentalo #etiquetala"}',
    ])
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=3000, messages=[{"role":"user","content":prompt}])
    texto = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
    s = texto.find("{")
    e = texto.rfind("}")
    if s >= 0 and e > s:
        cand = texto[s:e+1]
        try:
            return json.loads(cand)
        except:
            cand2 = cand.replace(chr(10)," ").replace(chr(13),"")
            try:
                return json.loads(cand2)
            except:
                cand3 = cand2.replace(chr(34)+chr(34),chr(34)+"'")
                return json.loads(cand3)
    raise ValueError("No JSON")
def descargar_musica():
    os.makedirs("musica", exist_ok=True)
    path = "musica/background.mp3"
    if os.path.exists(path) and os.path.getsize(path) > 100000:
        return path
    for url in ["https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3","https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"]:
        try:
            r = requests.get(url, timeout=30)
            if r.status_code==200 and len(r.content)>100000:
                open(path,"wb").write(r.content)
                return path
        except:
            continue
    return None
def generar_imagen(prompt_visual, nombre, base):
    headers = {"Authorization":"Bearer "+KIE_KEY,"Content-Type":"application/json"}
    payload = {"model":"bytedance/seedream-v4-text-to-image","input":{"prompt":prompt_visual,"image_size":"portrait_16_9","image_resolution":"1K","max_images":1}}
    r = requests.post(BASE_URL+"/api/v1/jobs/createTask",headers=headers,json=payload,timeout=60)
    if r.status_code!=200 or r.json().get("code")!=200:
        print("Error imagen: "+r.text[:100])
        return None
    task_id = r.json()["data"]["taskId"]
    print("Task: "+task_id)
    for i in range(60):
        time.sleep(5)
        r2 = requests.get(BASE_URL+"/api/v1/jobs/recordInfo?taskId="+task_id,headers=headers,timeout=15)
        if r2.status_code==200:
            d = r2.json().get("data",{})
            state = d.get("state","")
            print(state+" ("+str(i*5)+"s)")
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
def agregar_texto(img_path, drama):
    img = Image.open(img_path).convert("RGBA")
    w,h = img.size
    ov = Image.new("RGBA",(w,h),(0,0,0,0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0,0,w,170],fill=(0,0,0,205))
    d.rectangle([0,h-290,w,h],fill=(0,0,0,215))
    img = Image.alpha_composite(img,ov).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        fl = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",42)
        ft = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",50)
        fb = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",32)
        fs = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",27)
    except:
        fl=ft=fb=fs=ImageFont.load_default()
    draw.text((w//2,48),"LE CHISME",fill="#C9A84C",font=fl,anchor="mm")
    draw.text((w//2,108),"@lechisme.oficial",fill="#aaaaaa",font=fs,anchor="mm")
    titulo = drama.get("titulo","")
    palabras = titulo.split()
    lineas,linea = [],""
    for p in palabras:
        test = (linea+" "+p).strip()
        if len(test)<22:
            linea = test
        else:
            if linea: lineas.append(linea)
            linea = p
    if linea: lineas.append(linea)
    y = h-280
    for l in lineas:
        draw.text((w//2,y),l,fill="#C9A84C",font=ft,anchor="mm")
        y += 56
    preg = drama.get("pregunta_polemica","")
    if len(preg)>48:
        mid = preg.rfind(" ",0,48)
        draw.text((w//2,h-95),preg[:mid],fill="#ffffff",font=fb,anchor="mm")
        draw.text((w//2,h-55),preg[mid:],fill="#ffffff",font=fb,anchor="mm")
    else:
        draw.text((w//2,h-70),preg,fill="#ffffff",font=fb,anchor="mm")
    draw.text((w//2,h-15),"Comenta y Etiqueta a alguien",fill="#C9A84C",font=fs,anchor="mm")
    out = img_path.replace(".jpg","_texto.jpg")
    img.save(out,quality=95)
    return out
def crear_video(img_path, nombre, base):
    musica = descargar_musica()
    out = base+"/videos/"+nombre+".mp4"
    if musica:
        cmd = ["ffmpeg","-y","-loop","1","-i",img_path,"-i",musica,"-c:v","libx264","-tune","stillimage","-c:a","aac","-b:a","192k","-pix_fmt","yuv420p","-t","30","-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2","-af","volume=0.5",out]
    else:
        cmd = ["ffmpeg","-y","-loop","1","-i",img_path,"-c:v","libx264","-tune","stillimage","-pix_fmt","yuv420p","-t","30","-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",out]
    res = subprocess.run(cmd,capture_output=True)
    if res.returncode==0:
        return out
    return None
def publicar(universo_key, slot="manana"):
    base = get_carpeta_semana()
    numero = get_numero(base)
    dia_nombre = DIAS[datetime.now().weekday()]
    hora = HORARIOS_SLOT.get(slot,"00:00")
    prefijo = str(numero).zfill(2)+"_"+dia_nombre+"_"+hora.replace(":","h")
    print("EP #"+str(numero)+" | "+dia_nombre+" "+hora+" | "+universo_key)
    drama = generar_drama(universo_key)
    titulo = drama.get("titulo","")
    print("Titulo: "+titulo)
    print("\nHISTORIA:\n"+drama.get("historia_completa",""))
    print("\nPREGUNTA: "+drama.get("pregunta_polemica",""))
    print("\nTIKTOK:\n"+drama.get("caption_tiktok",""))
    print("\nINSTAGRAM:\n"+drama.get("caption_instagram",""))
    print("\nHASHTAGS:\n"+drama.get("hashtags",""))
    img = generar_imagen(UNIVERSOS[universo_key]["visual"],prefijo+"_raw",base)
    img_final = video = None
    if img:
        img_final = agregar_texto(img,drama)
        slug = "".join(c for c in titulo.lower()[:25].replace(" ","_") if c.isalnum() or c=="_")
        nombre_final = prefijo+"_"+slug
        img_path = base+"/imagenes/"+nombre_final+".jpg"
        os.rename(img_final,img_path)
        img_final = img_path
        video = crear_video(img_final,nombre_final,base)
    pub = {"numero":numero,"dia":dia_nombre,"hora":hora,"titulo":titulo,"historia_completa":drama.get("historia_completa",""),"pregunta":drama.get("pregunta_polemica",""),"caption_tiktok":drama.get("caption_tiktok",""),"caption_instagram":drama.get("caption_instagram",""),"hashtags":drama.get("hashtags",""),"imagen":img_final,"video":video}
    slug = "".join(c for c in titulo.lower()[:25].replace(" ","_") if c.isalnum() or c=="_")
    open(base+"/publicaciones/"+prefijo+"_"+slug+".json","w",encoding="utf-8").write(json.dumps(pub,ensure_ascii=False,indent=2))
    print("\nARCHIVOS EN: "+base)
    if video and os.path.exists(video):
        subprocess.run(["open",video])
    elif img_final and os.path.exists(img_final):
        subprocess.run(["open",img_final])
    subprocess.run(["open",base])
    return pub
def generar_dia():
    import random
    dia = datetime.now().weekday()
    regulares = [k for k in UNIVERSOS if k!="famoso"]
    es_famoso = dia in [0,2,4,6]
    for universo,slot in [(random.choice(regulares),"manana"),(random.choice(regulares),"tarde"),("famoso" if es_famoso else random.choice(regulares),"noche")]:
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
