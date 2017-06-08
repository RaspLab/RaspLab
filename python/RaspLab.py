## IMPORT

from flask import Flask, render_template, request, flash, redirect, url_for
from datetime import datetime
from utils import *
import json, time, os, requests, threading, subprocess, psutil, random, re, threading, socket
from werkzeug.utils import secure_filename
from subprocess import Popen, PIPE

## SITO
app = Flask(__name__)
settings = json.loads(open(real_path("common/settings.json"), "r").read())
cache = json.loads(open(real_path("common/cache.json"), "r").read())
app.secret_key = 'some_secret'

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['ppm', ])

## VARIABILI
server_ip = "localhost"

download_thread = None
global change
global on
global on2
hostname = socket.gethostname()
on = []
on2 = []
change = True
context = {
    "state": 0,  # 1: Acceso, 0: Spento
    "last_update": cache.get("last_update", datetime.now().timestamp())
}


orarioSettimanale={}
ore=[]





## FUNZIONI



@app.before_first_request
def startup():
    reload_dynamic_setting()


@app.route('/')
def index():
    content = {
        "last_update": pretty_date(datetime.fromtimestamp(context['last_update'])),
        "state": context['state'],
        "dynamic_load": settings.get('dynamic_load', False),
        "aula": settings.get('aula','None')
    }
    return render_template('index.html', **content)


@app.route('/update/text', methods=['POST'])
def update_text():
    data=[]
    data.append(request.form['text'])
    riga2 = None
    riga2valid = False
    if request.form['text2'] != "":
        data.append(request.form['text2'])
        riga2valid = True

    fn_kill_process(on)
    iter=0
    for i in data:
        args={"c" : "ff0000",\
              "m" : str(text_speed(i))}
        #_s00abcdef
        if bool(re.match(r'{.*}',i)):
                       
            args_str = re.search(r"\{(.+)\}", i)
            args_str = args_str.group(1) if args_str else None
            i = i.replace('{' + args_str + '}', '')
            args_str = args_str.replace(' ', '')
            for j in args_str.split(";"):
                data=j.split("=")
                args[data[0]]=data[1]
                print(args)
            
        speed=args['m']
        ln=32//len(data)
        fname=str(iter)
        red, green, blue = int(args['c'][0:2],16),int(args['c'][2:4],16),int(args['c'][4:6],16)
        image_generator(i,filename=fname,fontsize=ln,padding=iter*ln,font = "vcr",color = (red, green, blue), paddingX = False)
        
        p=Popen('sudo ../demo -D 1 gen/{filename}.ppm --led-no-hardware-pulse --led-rows=32 --led-chain=1 -m {duration}'.format(filename=fname,duration=speed),shell=True,stdout=PIPE)
        on.append(p)
        iter+=1
    flash('text')

    
    
    context['state'] = 1
    save_info(settings, cache)
    update_time(settings, cache, context)

    
    return redirect(url_for('index'))


@app.route('/update/image', methods=['POST'])
def update_image():
    print(request.files['file'].filename)
    context['state'] = 1
    save_info(settings, cache)
    update_time(settings, cache, context)
    if 'file' not in request.files:
        flash('error')
    file = request.files['file']
    if file.filename == '':
        flash('error')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('image')
    else:
        flash('error')
    fn_kill_process(on)
    p=Popen('sudo ../demo -D 1 uploads/{filename} --led-no-hardware-pulse --led-rows=32 --led-chain=2'.format(filename=filename),shell=True,stdout=PIPE)
    on.append(p)
    
    
    return redirect(url_for('index'))





@app.route('/quicksettings', methods=['POST'])
def quicksettings():
    dynamic_load = bool(request.form.get('dynamic_load'))
    settings['dynamic_load'] = dynamic_load
    save_info(settings, cache)
    reload_dynamic_setting()
    return redirect(url_for('index'))


@app.route('/stop', methods=['POST'])
def stop():
    bring_down_state(context, settings, cache)
    fn_kill_process(on)
    return redirect(url_for('index'))


@app.route('/update/aula', methods=['POST'])
def update_aula():
    settings['aula'] = request.form['aula']
    save_info(settings, cache)
    return redirect(url_for('index'))

@app.route('/cmd', methods=['POST'])
def cmd():
    print(request.form['cmd'])
    return redirect(url_for('index',_anchor='cmd_form'))



def reload_dynamic_setting():
    global orarioSettimanale
    global ore
    domenica = '0'
    global change
    global download_thread
    dynamic = settings.get('dynamic_load', False)
    fn_kill_process(on)
    fn_kill_process(on2)
    change = False
    download_success = False
    already_started = True
    if dynamic:
        while not download_success:
            try:
                orarioSettimanale = json.loads(requests.get('http://{}:5001/get/'.format(server_ip) + settings['aula']).text)
                ore = json.loads(requests.get('http://{}:5001/get/'.format(server_ip) + 'ore').text)["hour"]
                download_success = True
            except:
                orarioSettimanale = None
                ore = None
                sDomenica = 'errore'
                speed = 30
                domenica = '0'
                if already_started:
                    already_started=False
                    p = Popen('sudo ../demo -D 1 gen/{filename}.ppm --led-no-hardware-pulse --led-rows=32 --led-chain=1 -m {duration}'.format(filename=sDomenica,duration=speed),shell=True,stdout=PIPE)
                time.sleep(3)
        fn_kill_process([p])        
        day = getDay()
        hours = int(getHours())
        print(hours)
            
        if day != domenica:
            
            print("DYNAMIC")

            for i in range(len(ore)):
                print(hours, ore[i][0], ore[i][1])
                if hours >= ore[i][0] and hours < ore[i][1]:
                    if orarioSettimanale[day][ore.index(ore[i])] != []:
                        context['state'] = 1
                        download_thread = threading.Thread(target=fn_matrix, args=(orarioSettimanale[day][ore.index(ore[i])][0], orarioSettimanale[day][ore.index(ore[i])][1], orarioSettimanale[day][ore.index(ore[i])][2]))
                        download_thread.start()

                        changeHour = int(str(ore[i][1]).split('.')[1])
                        minute = int(getMinutes())
                        while  minute < changeHour:
                            timeSleep = changeHour - minute

                            time.sleep(timeSleep//2 + 1)

                            minute = int(getMinutes())
                        change = False
                    
                    else:
                        buche = False
                    print('dddddd')
                else:
                    buche = True
            if buche:
                fn_orebuche()
        else:
            fn_Sunday()

def fn_orebuche():
    print('CLASSE LIBERA')
    

def getHours():
    return datetime.today().strftime('%H')

def getMinutes():
    return datetime.today().strftime('%M')

def fn_Sunday():
    sDomenica = 'sunday'
    speed = 30
    domenica = '0'
    
    p = Popen('sudo ../demo -D 1 gen/{filename}.ppm --led-no-hardware-pulse --led-rows=32 --led-chain=1 -m {duration}'.format(filename=sDomenica,duration=speed),shell=True,stdout=PIPE)
    time.sleep(3)
    while getDay() == domenica:
        time.sleep(3600)
        print('ciao')
    fn_kill_process([p])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def image_generator(text, **kwargs):
    import os
    from PIL import ImageFont
    from PIL import Image
    from PIL import ImageDraw
     

    addSpace = 2
    font = ImageFont.truetype("static/fonts/{}.ttf".format(kwargs.get('font',"vcr")), kwargs.get('fontsize', 32))
    
    text_split = text.split(' ')
    v_tuple = []
    for i in range(len(text_split)):
        text_split[i] += " "
        #v_tuple.append((text_split[i], (random.randint(0,255), random.randint(0,255), random.randint(0,255))))
        v_tuple.append((text_split[i], kwargs.get('color', (255,0,0))))
    
  
    
    all_text = ""
    for text_color_pair in v_tuple:
        t = text_color_pair[0]
        all_text = all_text + t
 
    width, ignore = font.getsize(all_text)
 
 
    im = Image.new("RGB", (width + 15, kwargs.get('height',32)), "black")
    draw = ImageDraw.Draw(im)
 
    x = 0;
    for text_color_pair in v_tuple:
        t = text_color_pair[0]
        c = text_color_pair[1]
        paddX = 0
        if kwargs.get('paddingX', False):
            paddX = ((32-font.getsize(t)[0])//2) + addSpace
            print(paddX, font.getsize(t)[0])
        print('PADDING: ', kwargs.get('padding',0))
        draw.text((x + paddX, kwargs.get('padding',0)), t, c, font=font)
        x = x + font.getsize(t)[0]
     
    im.save("gen/{}.ppm".format(kwargs.get('filename',"default")))




def getDay():
    return time.strftime("%w")

def text_speed(text):
    res = len(text)*3
    res = res if res>=14 else 14
    res = res if res<=22 else 22
    return res



def fn_kill_process(v):
    
    import psutil

    
    for p in v: 
        parent_pid = p.pid   # my example
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):  # or parent.children() for recursive=False
            child.kill()
        parent.kill()
    del v[:]
    


def fn_matrix(classe = '', subject = '', vProf = []):
    global change
    prof = ''
    for s in vProf:
        prof += '    ' + s
    
    width = 32
    hight = 32
    fontText = "Roboto-Regular"
    nRighe = 2

    fontSize = (hight//nRighe) -3
    controlTime = float('{0:.1f}'.format(fontSize/30))
    print(controlTime)
    prof = '  ' + prof
    changeTime =  controlTime * len(prof) 
    
    prof ='   ' + prof
    time.sleep(controlTime)

    classImage = 'classe'
    classPadding = 0
    classColor = (0, 250, 0)
    classSpeed = 0
    
    image_generator(classe,filename=classImage, fontsize = hight//nRighe, padding = classPadding, font = fontText, color = classColor, paddingX = True)

    
    p=Popen('sudo ../demo -D 1 gen/{filename}.ppm --led-no-hardware-pulse --led-rows=32 --led-chain=1 -m {duration}'.format(filename=classImage, duration=classSpeed),shell=True,stdout=PIPE)
    on.append(p)

    sub_profPadding = 16
    diz = {'profImage' : 'prof',
           'subjectImage' : 'materia',
           
           'subjectColor' : (0, 250 ,0),
           'profColor' : (0, 250 , 0),
           
           'subjectSpeed' : 0,
           'profSpeed' : 50
           }
    image_generator(prof, filename = diz['profImage'], fontsize = fontSize, padding = sub_profPadding, font = fontText, color = diz['profColor'], paddingX = False)
    image_generator(subject, filename = diz['subjectImage'], fontsize = fontSize, padding = sub_profPadding, font = fontText, color = diz['subjectColor'], paddingX = True)
    
    
    
    pre = 'subject'
    
    change = True
    p = ''
    while change:
        if p != '':
            on2.remove(p)
        p = Popen('sudo ../demo -D 1 gen/{filename}.ppm --led-no-hardware-pulse --led-rows=32 --led-chain=1 -m {duration} -t {time}'.format(filename = diz[pre + 'Image'], duration= diz[pre + 'Speed'], time = changeTime),shell=True,stdout=PIPE)

        on2.append(p)

        if pre == 'subject':
            pre = 'prof'
        else:
            pre = 'subject'
        
        cont = 0
        while cont < changeTime and change:
            
            time.sleep(controlTime)
            cont += controlTime
    print('..................................caiuiddhcdhfuwehfweuidfh...........................')
    fn_kill_process(on)
    fn_kill_process(on2)

    
    


if __name__ == '__main__':
    print(getHours(), getMinutes())
    start_runner()
    app.run(debug=True,host="0.0.0.0")
    
