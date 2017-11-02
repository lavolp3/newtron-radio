#!/usr/bin/python2.7
# coding=utf-8

# Wenn enable_gpio auf True gesetzt wird, muss das Radio
# mit root-Rechten gestartet werden (sudo)
enable_gpio = False
if enable_gpio:
    import RPi.GPIO as GPIO
import pygame
from pygame.locals import *
from kaa import imlib2
from random import randint
import json
from operator import itemgetter
import urllib2
import datetime
import sys
import os
import pwd
import grp
import re
import shutil
import socket
import subprocess
import mpd

##### Pfade und Environment ################################
# Umgebungsvariablen für den Konsolenmodus

if not os.getenv('SDL_FBDEV'):
    os.environ["SDL_FBDEV"] = "/dev/fb1"
if not os.getenv('SDL_MOUSEDEV'):
    os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
if not os.getenv('SDL_MOUSEDRV'):
    os.environ["SDL_MOUSEDRV"] = "TSLIB"

if not os.getenv("TSLIB_FBDEVICE"):
    os.environ["TSLIB_FBDEVICE"] = os.getenv('SDL_FBDEV')
if not os.getenv("TSLIB_TSDEVICE"):
    os.environ["TSLIB_TSDEVICE"] = os.getenv('SDL_MOUSEDEV')

# Pfad zur Konfigurationsdatei
Home=pwd.getpwuid(os.getuid()).pw_dir
ConfigPath = os.path.join(Home,".config")
ConfigFile = os.path.join(ConfigPath,"newtron-radio.conf")

# Pfad zum Programmverzeichnis
ScriptPath = os.path.dirname(__file__)

##### Skin #################################################
# Zu verwendender Skin (default: 'Tron')
# Mitgelieferte Skins: 'Tron', 'Copper' und 'Flat'
skin = 'Tron'

# Starte mit Hauptanzeige (menu = 1)
menu = 1

##### Bildschirm ###########################################
# Bildschirmgrösse (fbcon)
# nur setzen, wenn die Automatik nicht geht!
#w=320
#h=240

# Bildschimgrösse (für X-Display)
Showcursor = True
Fullscreen = False
# X-Aufloesung, wenn Fullscreen = False
x_w = 320
x_h = 240

##### Screensaver & Wetter ################################
# OpenWeatherMap city-ID - gibt den Ort für die Wetterdaten an
# Zu ermitteln über http://openweathermap.org
OWM_ID = '2925533' # Frankfurt
# API-Key für die OpenWeatherMap API
# Der Key kann einfach über http://openweathermap.org/appid
# angefordert werden. Der Key ist hier als String anzugeben
# OWM_KEY = '1234567890abcdef1234567890abcdef'
OWM_KEY = None

# Mögliche Werte sind 'clock', 'weather', 'black' oder 'off'
screensaver_mode = 'clock'
screensaver_timer = 10  # in Minuten; Zeit bis Screensaver aktiv wird
screensaver = False     # wenn True, starte mit aktiviertem Screensaver

##### GPIO-Konfiguration fürs Backlight ####################
# Normalerweise müssen im Programmcode selbst
# noch weitere Anpassungen vorgenommen werden
if enable_gpio:
    screensaver_mode = 'black'
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    bl_on = GPIO.HIGH   # Signal dass das Backlight aktiviert
    bl_off = GPIO.LOW   # Signal dass das Backlight deaktiviert
    if screensaver:
        GPIO.output(18, bl_off)
    else:
        GPIO.output(18, bl_on)

###### W-LAN Device ########################################
# Welches device soll für die Empfangsstärkenanzeige
# verwendet werden.
wlan_device = 'wlan0'

###### Playlistenmanagement ################################
# Vollständiger Pfad zur mpd.conf
mpd_config = '/etc/mpd.conf'
defaultplaylist = 'Radio BOB!' # eine Playlist aus dem 'playlist_directory'
sort_playlists = True

# Name der Datei in die die aktuelle Playliste
# gespeichert werden soll (mpc.save())
save_filename = 'saved_playlist'

# Zeige das 'X' auf der Hauptseite zum Entfernen
# des aktuellen Playlisteneintrags
x_button = False

# Zeige das '+' auf der Playlist-Seite zum Hinzufügen
# des aktuellen Verzeichnisses zur Playliste
plus_button = True

##### Diverse weitere Konfiguration ########################

# Default, wenn kein Font in skin.cfg angegeben ist
skin_font = None

# Wenn ein durchsichtiger skin verwendet wird kann
# text_on_top auf 'False' gesetzt werden um den Text
# so scheinen zu lassen, als ob er sich unterhalb
# der Skinoberfläche befindet
text_on_top = True

# Wenn 'True' wird die Lesbarkeit von hellem Text auf hellem
# Hintergrund durch einen Schatteneffekt des Textes verbessert
dropshadow = False

#max. Framerate
FPS = 5

# Globale Variablen
FiveSecs = False
OneSec = False
TenMins = True
Refresh = True
Dirty = True
btn_update_flag = True
status_update_flag = False
pb_page = False

# Globale Variablen zum Speichern der alten Werte
# um festzustellen, ob sich was geändert hat
# Werden nur in "update_screen()" verwendet
Station = ""
Title = ""

# Audioausgabevariablen
# Der hier gesetzte Wert von oldvol wird nur verwendet,
# wenn beim Start die Lautstärkeinfo vom mpd nicht geholt
# werden kann
oldvol = 80
muted = False

# Einstellungen fürs Eventhandling
if screensaver:
    minutes = screensaver_timer
else:
    minutes = 0
seconds = 0

###### Farbmanagement ######################################
#colors     R    G    B
white   = (255,255,255)
lgrey   = (160,160,160)
red     = (255,  0,  0)
green   = (  0,255,  0)
blue    = (  0,  0,255)
black   = (  0,  0,  0)
cyan    = (  0,255,255)
magenta = (255,  0,255)
yellow  = (255,255,  0)
orange  = (255,127,  0)
folder  = (224,144, 64)
dark_green = (  0,128,  0)
mp3_green  = (  0,224,  0)
pls_cyan   = (  0,224,224)
dark_blue  = (  0,  0, 48)
dark_grey  = ( 32, 32, 32)
tron_blue  = (  0,150,200)

# Defaultfarben bei fehlender "skin.cfg"
font_color = tron_blue
shadow_color = dark_grey
skin_color = tron_blue
weather_bg_color = dark_blue
bg_color = black

# Farben für die Datei-/Playlistenanzeigen
pls_color = pls_cyan        # für Playlisten im music-dir
dir_color = folder      # für Verzeichnisse
mp3_color = mp3_green       # für Dateien
rad_color = tron_blue   # für playlisten im playlists-dir
err_color = red         # für Playlistauswahlfehler

###### Touchbutton + Skin Dateien ##########################
msg_frame = "Status.svg"
btn_list = [
    "Stop.svg",
    "Pause.svg",
    "Up.svg",
    "Mute.svg",
    "Prev.svg",
    "Next.svg",
    "Down.svg",
    "Next_Page.svg",
    "Cloud.svg",
    "Color.svg",
    "Exit.svg",
    "Quit.svg",
    "Poweroff.svg",
    "Reboot.svg",
    "Refresh.svg",
    "Play.svg",
    "Unmute.svg",
    "Empty.svg",
    "Plug.svg",
    "Enter.svg",
    "Updir.svg",
    "Prev_Page.svg",
    "Trash.svg",
    "Save.svg",
    "Shuffle.svg",
    "Config.svg"]
wlan_list = [
    "wlan000.svg",
    "wlan025.svg",
    "wlan050.svg",
    "wlan075.svg",
    "wlan100.svg"]
chk_list =[
    "Checkbox.svg",
    "Checkbox_Sel.svg",
    "Checkbox_down.svg",
    "Checkbox_up.svg"]
selection_frame = "Selection.svg"
select_pl = "Playlist_msg.svg"

##### Funktions- und Klassendefinitionen ###################

def disp_init(): # (Automatische) Erkennung des Displays
    global w,h,size
    disp_found = False
    x_disp = os.getenv('DISPLAY')
    if x_disp:
        print 'using X-Display ' + os.getenv('DISPLAY')
        try:
            os.putenv('SDL_VIDEODRIVER','x11')
            pygame.display.init()
            pygame.display.set_caption('NewTRON-Radio v2.x','NewTRON-Radio')
            if (Showcursor):
                pygame.mouse.set_visible(True)
            else:
                pygame.mouse.set_cursor((8,8),(4,4),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
            if (Fullscreen):
                info = pygame.display.Info()
                w = info.current_w
                h = info.current_h
            else:
                w = x_w
                h = x_h
            disp_found = True
        except:
            print 'Problem with X11-Driver!'
            pygame.display.quit()
    elif os.getenv('SDL_VIDEODRIVER'):
        print 'using ' + os.getenv('SDL_VIDEODRIVER') + ' from SDL_VIDEODRIVER env var.'
        try:
            pygame.display.init()
            pygame.mouse.set_visible(False)
            disp_found = True
        except:
            e, v = sys.exc_info()[:2]
            print str(e) + ': ' + str(v)

            print 'Driver ' + os.getenv('SDL_VIDEODRIVER') + ' from SDL_VIDEODRIVER env var failed!'
            print 'Is your SDL_VIDEODRIVER entry correct?'
            print 'Also check:'
            print('SDL_FBDEV = ' + os.getenv('SDL_FBDEV'))
            print('SDL_MOUSEDEV = ' + os.getenv('SDL_MOUSEDEV'))
            print('SDL_MOUSEDRV = ' + os.getenv('SDL_MOUSEDRV'))
            print('Are theese correct? Set them in Line 30ff.')
            pygame.display.quit()
    else:
        print 'trying fbcon'
        os.putenv('SDL_VIDEODRIVER','fbcon')
        try:
            pygame.display.init()
            pygame.mouse.set_visible(False)
            print 'using ' + pygame.display.get_driver()
            disp_found = True
        except:
            e, v = sys.exc_info()[:2]
            print str(e) + ': ' + str(v)

            print('Driver fbcon failed!')
            print('Is libts/libts-bin installed?')
            print 'Also check:'
            print('SDL_FBDEV = ' + os.getenv('SDL_FBDEV'))
            print('SDL_MOUSEDEV = ' + os.getenv('SDL_MOUSEDEV'))
            print('SDL_MOUSEDRV = ' + os.getenv('SDL_MOUSEDRV'))
            print('Are theese correct? Set them in Line 30ff.')
            pygame.display.quit()

    if disp_found:
        try: w or h
        except:
            w = pygame.display.Info().current_w
            h = pygame.display.Info().current_h
        size = (w, h)
    else:
        if enable_gpio:
            GPIO.cleanup()
        raise Exception('No suitable video driver found!')

def reboot():
    screen.fill(bg_color)
    reboot_label = title_font.render("Reboot...", 1, (font_color))
    screen.blit(reboot_label,
        reboot_label.get_rect(center=(w/2, h/2))
    )
    pygame.display.flip()
    pygame.time.wait(5000)
    pygame.quit()
    subprocess.call('sudo reboot' , shell=True)

def poweroff():
    screen.fill(bg_color)
    poweroff_label = title_font.render("Shutdown...", 1, (font_color))
    screen.blit(poweroff_label,
        poweroff_label.get_rect(center=(w/2, h/2))
    )
    pygame.display.flip()
    pygame.time.wait(5000)
    pygame.quit()
    subprocess.call('sudo poweroff' , shell=True)

def waiting(msg_text1='please wait...',msg_text2=None):
    screen.fill(bg_color)
    text_label = title_font.render(msg_text1, 1, (font_color))
    if msg_text2 == None:
        screen.blit(text_label, text_label.get_rect(center=(w/2, h/2)))
    else:
        screen.blit(text_label, text_label.get_rect(center=(w/2, h/2-text_label.get_height()/2)))
        text_label = title_font.render(msg_text2, 1, (font_color))
        screen.blit(text_label, text_label.get_rect(center=(w/2, h/2+text_label.get_height()/2)))
    pygame.display.flip()

def draw_text(win,text,font,color,align='topleft',pos=(0,0)):
    label = font.render(text,1,color)
    label_pos=label.get_rect()
    if align == 'centerx':
        label_pos.centerx=win.get_rect().centerx
    if align == 'topright':
        label_pos.topright=win.get_rect().topright
    if dropshadow:
        label_shadow = font.render(text,1,shadow_color)
        win.blit(label_shadow,(label_pos[0]+pos[0]+1,label_pos[1]+pos[1]+1))
    win.blit(label,(label_pos[0]+pos[0],label_pos[1]+pos[1]))
    
def mpd_connect(client):
    try:
        client.connect("/var/run/mpd/socket", 6600)
        print "connected using unix socket..."
    except mpd.ConnectionError as e:
        if str(e) == 'Already connected':
            print 'trying to reconnect...'
            # Das folgende disconnect() schlägt fehl (broken pipe)
            # obwohl von python_mpd2 'Already connected' gemeldet wurde
            # Aber erst ein auf das disconnect() folgender connect()
            # ist erfolgreich...
            try:
                client.disconnect()
                pygame.time.wait(1500)
                mpd_connect(client)
            except socket.error:
                mpd_connect(client)
    except socket.error as e:
        # socket.error: [Errno 111] Connection refused
        # socket.error: [Errno 2] No such file or directory
        # print str(e)
        try:
            # Nötig, um einen 'service mpd restart' zu überstehen
            pygame.time.wait(1500)
            client.connect("localhost", 6600)
            print "connected using localhost:6600"
        except:
            e, v = sys.exc_info()[:2]
            print str(e) + ': ' + str(v)
            print "restarting mpd..."
            subprocess.call("sudo service mpd restart", shell=True)
            pygame.time.wait(1500)
            mpd_connect(client)

def save_config():
    if not os.path.isdir(ConfigPath):
        try:
           os.mkdir(ConfigPath)
        except:
            print 'Failed to create ' + ConfigPath
    with open(ConfigFile,'w') as f:
        f.write('skin='+skin+'\n')
        f.write('screensaver_mode='+screensaver_mode+'\n')
        f.write('screensaver_timer='+str(screensaver_timer)+'\n')
        f.write('x_button='+str(x_button)+'\n')
        f.write('plus_button='+str(plus_button)+'\n')
        f.write('fullscreen='+str(Fullscreen)+'\n')

def read_config():
    global skin, Fullscreen
    global screensaver_mode
    global screensaver_timer
    global x_button, plus_button
    if os.path.isfile(ConfigFile):
        with open(ConfigFile) as f:
            for l in f:
                if len(l.split('=')) > 1:
                    key = l.strip().split('=')[0].lower().rstrip()
                    value = l.strip().split('=')[1].split('#')[0].strip()
                    if value:
                        if key == 'skin':
                            skin = value.strip("\'\"")
                        elif key == 'screensaver_mode':
                            screensaver_mode = value.strip("\'\"")
                        elif key == 'screensaver_timer':
                            screensaver_timer = eval(value)
                        elif key == 'x_button':
                            x_button = eval(value)
                        elif key == 'plus_button':
                            plus_button = eval(value)
                        elif key == 'fullscreen':
                            Fullscreen = eval(value)
    else:
        print 'No ConfigFile found, using defaults'

def get_config():
    draw_text(msg_win,'NewTron-Radio Settings',status_font,status_color,align='centerx')
    if x_button:
        chk_win[0].blit(chk_buf[1],(0,0))
    else:
        chk_win[0].blit(chk_buf[0],(0,0))
    draw_text(chk_win[0],' X-Button',status_font,font_color,pos=(chk_buf[0].get_width(),0))
    if plus_button:
        chk_win[1].blit(chk_buf[1],(0,0))
    else:
        chk_win[1].blit(chk_buf[0],(0,0))
    draw_text(chk_win[1],' Plus-Button',status_font,font_color,pos=(chk_buf[0].get_width(),0))
    if Fullscreen:
        chk_win[2].blit(chk_buf[1],(0,0))
    else:
        chk_win[2].blit(chk_buf[0],(0,0))
    draw_text(screen,' Fullscreen (Save & Restart required)',status_font,font_color,pos=(chk_win[2].get_abs_offset()[0] + chk_buf[0].get_width(), chk_win[2].get_abs_offset()[1]))
    draw_text(screen,'Skin-Name: ' + skin,status_font,font_color,align='centerx',pos=(0,chk_win[4].get_abs_offset()[1]))
    draw_text(status_win,'Screensaver: ' + screensaver_mode + ' (' + str(screensaver_timer) + 'min)',status_font,status_color,align='centerx')

def set_config(idx=None):
    global screensaver_mode
    global x_button, plus_button, Fullscreen
    global Refresh
    if idx == 0: x_button = x_button^True
    if idx == 1: plus_button = plus_button^True
    if idx == 2 or idx == 3: Fullscreen = Fullscreen^True

    if idx == 9:
        ss_mode = [ 'clock' , 'weather' , 'black' , 'off' ]
        ss_idx = ss_mode.index(screensaver_mode) + 1
        if ss_idx >= len(ss_mode):
            ss_idx = 0
        screensaver_mode=(ss_mode[ss_idx])
    Refresh = True

def read_skin_config():
    global font_color, skin_color, status_color, shadow_color
    global bg_color, weather_bg_color, weather_font_color, clock_font_color
    global skin_font, text_on_top, dropshadow
    global font_size, status_font_size, title_font_size, clock_font_size
    global font, status_font, title_font, clock_font
    global wallpaper, weather_wallpaper
    status_color = None
    weather_font_color = None
    clock_font_color = None
    wallpaper = None
    weather_wallpaper = None
    skin_font = None
    # Default-Fontgrössen, wenn kein Font angegeben wurde
    font_size = h/14
    status_font_size = h/11
    title_font_size = h/8
    clock_font_size = h/3
    skin_config = os.path.join(SkinPath,"skin.cfg")
    if os.path.isfile(skin_config):
        # Setze Default-Fontgrössen, wenn ein Font angegeben wurde
        with open(skin_config) as f:
            for l in f:
                if len(l.split('=')) > 1:
                    if l.strip().split('=')[0].lower().rstrip() == 'skin_font':
                        value = l.strip().split('=')[1].split('#')[0].strip()
                        if value:
                            if os.path.isfile(value.strip("\'\"")):
                                skin_font = value.strip("\'\"")
                                font_size = h/21
                                status_font_size = h/17
                                title_font_size = h/12
                                clock_font_size = h/4
        # Lese den Rest der Konfiguration ein
        with open(skin_config) as f:
            for l in f:
                if len(l.split('=')) > 1:
                    key = l.strip().split('=')[0].lower().rstrip()
                    value = l.strip().split('=')[1].split('#')[0].strip()
                    if value:
                        if key == 'font_color':
                            font_color = eval(value)
                        elif key == 'background_color':
                            bg_color = eval(value)
                        elif key == 'weather_background_color':
                            weather_bg_color = eval(value)
                        elif key == 'weather_font_color':
                            weather_font_color = eval(value)
                        elif key == 'skin_color':
                            skin_color = eval(value)
                        elif key == 'status_color':
                            status_color = eval(value)
                        elif key == 'clock_font_color':
                            clock_font_color = eval(value)
                        elif key == 'shadow_color':
                            shadow_color = eval(value)
                        elif key == 'background':
                            if os.path.isfile(os.path.join(SkinPath,value.strip("\'\""))):
                                wallpaper = os.path.join(SkinPath,value.strip("\'\""))
                        elif key == 'weather_background':
                            if os.path.isfile(os.path.join(SkinPath,value.strip("\'\""))):
                                weather_wallpaper = os.path.join(SkinPath,value.strip("\'\""))
                        elif key == 'font_size':
                            font_size = eval(value)
                        elif key == 'status_font_size':
                            status_font_size = eval(value)
                        elif key == 'title_font_size':
                            title_font_size = eval(value)
                        elif key == 'clock_font_size':
                            clock_font_size = eval(value)
                        elif key == 'text_on_top':
                            text_on_top = eval(value)
                        elif key == 'dropshadow':
							dropshadow = eval(value)
    else:
        print "No skin.cfg found. trying defaults..."
    font = pygame.font.Font(skin_font, font_size)
    status_font = pygame.font.Font(skin_font, status_font_size)
    title_font = pygame.font.Font(skin_font, title_font_size)
    clock_font = pygame.font.Font(skin_font, clock_font_size)
    if not status_color:
        status_color = font_color
    if not weather_font_color:
        weather_font_color = font_color
    if not clock_font_color:
        clock_font_color = font_color

def get_skins():
    entries = []
    for dirs in os.walk(SkinBase):
        if 'skin.cfg' in dirs[2]:
            entries.append(os.path.basename(dirs[0]))
    return entries

def init_playlists():
    global ScriptPath
    # default playlistdir - DO NOT CHANGE!
    pl_dir = '/var/lib/mpd/playlists/'
    pl_src = os.path.join(ScriptPath,'playlists')
    # Versuche das mpd Playlisten Verzeichnis aus mpd.conf herauszulesen
    try:
        with open(mpd_config) as f:
            for l in f:
                if l.strip():
                    if l.strip().split()[0].lower() == 'playlist_directory':
                        pl_dir = l.strip().split()[1].strip("\'\"")
    except:
        print "mpd config file " + mpd_config + " not found, using defaults"

    # Existieren Playlists? wenn nicht, kopiere welche ins mpd playlists-dir
    if mpc.listplaylists() == []:
        print "copying some playlists to " + pl_dir
        # Mache das mpd Playlisten Verzeichnis für den Benutzer schreibbar
        scriptuserid=os.getuid()
        if not scriptuserid: # Script läuft nicht als 'root'
            # Scriptuser sollte im Normalfall der User 'pi' sein
            scriptuser=pwd.getpwuid(scriptuserid).pw_name
            if not scriptuser in grp.getgrnam('audio').gr_mem:
                # Der Scriptuser sollte Mitglied der Gruppe 'audio' sein
                subprocess.call("sudo usermod -a -G audio " + scriptuser, shell=True)
        if os.path.isdir(pl_dir):
            # Mache das mpd Playlisten Verzeichnis für
            # die Gruppe 'audio' beschreibbar
            subprocess.call("sudo chgrp audio " + pl_dir, shell=True)
            subprocess.call("sudo chmod g+rwxs " + pl_dir, shell=True)

        # Versuche die Beispiel-Radio-Playlisten ins
        # mpd Playlisten Verzeichnis zu kopieren
        try:
            if os.path.isdir(pl_dir) and os.path.isdir(pl_src):
                for i in os.listdir(pl_src):
                    shutil.copy2(os.path.join(pl_src,i), pl_dir)
            else:
                print "missing " + pl_dir + " or " + pl_src
            try: mpc.update()
            except: pass
        except:
            e, v = sys.exc_info()[:2]
            print str(e) + ': ' + str(v)
            print "failed to copy playlists!"

    # Ist vielleicht eine Playlist im mpd 'state'-file
    if int(mpc.status()['playlistlength']) > 0:
        if mpc.status()['state'] != 'play':
            mpc.play()
    else:
        try:
            mpc.load(defaultplaylist)
            mpc.play()
        except: pass

def get_playlists(dir='/'):
    entries = []
    try:
        files = mpc.lsinfo(dir)
    except:
        global Refresh
        global Dirty
        Refresh = True
        Dirty = True
        dir='/'
        files = mpc.lsinfo(dir)
    for i in range(len(files)):
        if 'directory' in files[i]:
            if files[i]['directory'][-4:].lower() == '.zip':
                next # zipfiles machen Probleme...
            else:
                entries.append(['d',files[i]['directory'],dir_color])
        if 'playlist' in files[i]:
            if files[i]['playlist'][-4:].lower() == '.m3u':
                entries.append(['p',files[i]['playlist'],pls_color])
            elif files[i]['playlist'][-4:].lower() == '.pls':
                next # .pls wird von mpd unter Raspbian nicht unterstützt
            else:
                entries.append(['p',files[i]['playlist'],rad_color])
        if 'file' in files[i]:
            entries.append(['f',files[i]['file'],mp3_color])
    if not entries:
        entries = [['e',dir + '/no playlists or files found ...',err_color]]
    if sort_playlists:
        entries.sort(key=itemgetter(0,1)) # sort ABCabcÄä
        # sort AÄaäBbCc (locale benötigt):
        # sort AaBbCcÄä (ohne locale):
        # entries.sort(key=itemgetter(1))
        # entries.sort(key=lambda x: locale.strxfrm(str.lower(x[1])))
        # entries.sort(key=itemgetter(0))
        # bzw. in einer Zeile:
        # entries = sorted(sorted(sorted(entries,key=itemgetter(1)),key=lambda x: locale.strxfrm(str.lower(x[1]))),key=itemgetter(0))
    return entries

def show_playlists(index=0):
    global playlists
    global Dirty
    old_len = len(playlists)
    playlists = get_playlists(os.path.dirname(playlists[index][1]))
    if len(playlists) != old_len:
        Dirty = True
    if len(playlists) == 0:
        draw_text(list_win[0],'no playlists found...',title_font,font_color)
        return False
    if len(playlists) > 3:
        draw_text(list_win[2],playlists[index-2][1].split('/')[-1],status_font,playlists[index-2][2])
    if len(playlists) > 1:
        draw_text(list_win[1],playlists[index-1][1].split('/')[-1],status_font,playlists[index-1][2])
    draw_text(list_win[0],playlists[index][1].split('/')[-1].replace('.m3u','',1),title_font,playlists[index][2])
    if len(playlists) > 2:
        draw_text(list_win[3],playlists[(index+1)%len(playlists)][1].split('/')[-1],status_font,playlists[(index+1)%len(playlists)][2])
    if len(playlists) > 4:
        draw_text(list_win[4],playlists[(index+2)%len(playlists)][1].split('/')[-1],status_font,playlists[(index+2)%len(playlists)][2])
    return True

def set_playlist(index):
    global playlists
    try:
        if playlists[index][0] == 'p':
            mpc.clear()
            mpc.load(playlists[index][1])
        elif playlists[index][0] == 'f':
            mpc.add(playlists[index][1])
        elif playlists[index][0] == 'd':
            playlists = get_playlists(playlists[index][1])
            return False
        elif playlists[index][0] == 'e': # Keine Playlisten oder Dateien gefunden
            playlists = get_playlists(os.path.dirname(playlists[index][1]))
            return False
    except:
        e, v = sys.exc_info()[:2]
        print 'set_playlist() ' + str(e) + ': ' + str(v)
        return False
    mpc.play()
    return True

def status_update(Info):
    # Zeitanzeige
    Status = mpc.status()
    try:
        Songtime = int(Info['time'])
        if Songtime == 0:
            raise KeyError
        sm, ss = divmod(Songtime, 60)
        sh, sm = divmod(sm, 60)
        Elapsed = int(Status['elapsed'].split('.')[0])
        em, es = divmod(Elapsed, 60)
        eh, em = divmod(em, 60)
        if not sh:
            hms_elapsed = "%02d:%02d" % (em, es)
            hms_songtime = "%02d:%02d" % (sm, ss)
        else:
            hms_elapsed = "%d:%02d:%02d" % (eh, em, es)
            hms_songtime = "%d:%02d:%02d" % (sh, sm, ss)
        time_text=hms_elapsed + '/' + hms_songtime
    except KeyError:
        time_text=datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    draw_text(status_win,time_text,status_font,status_color,align='centerx')
    # Lautstärkeanzeige
    volume = 'Vol.: ' + Status.get('volume', str(oldvol)) + '%'
    draw_text(status_win,volume,status_font,status_color)
    # Anzeige der Stück-/Stationsnummer
    pln = str(int(Info.get('pos','-1'))+1) + '/' + Status.get('playlistlength','0')
    draw_text(status_win,pln,status_font,status_color,align='topright')
    # Anzeige der Bitrate
    bitrate = Status.get('bitrate', '0') + 'kbps'
    draw_text(bitrate_win,bitrate,status_font,status_color,align='topright')

def get_xfade_state():
    draw_text(msg_win,'MPD Playback Settings',status_font,status_color,align='centerx')
    Status = mpc.status()
    if 'xfade' in Status:
        secs=Status['xfade']
        if secs == '0': xf_state = 'off' # für mpd unter 'wheezy'
        else: xf_state = secs + 's'
    else: xf_state = 'off'
    draw_text(screen,'Crossfade: ' + xf_state,status_font,font_color,align='centerx',pos=(0,chk_win[0].get_abs_offset()[1]))
    chk_win[0].blit(chk_buf[2],(0,0))
    chk_win[1].blit(chk_buf[3],(chk_win[5].get_width()-chk_buf[3].get_width(),0))

    mr_db = 'MixRamp threshold: ' + str(round(float(Status['mixrampdb']),1))+ 'dB'
    draw_text(screen,mr_db,status_font,font_color,align='centerx',pos=(0,chk_win[2].get_abs_offset()[1]))
    chk_win[2].blit(chk_buf[2],(0,0))
    chk_win[3].blit(chk_buf[3],(chk_win[3].get_width()-chk_buf[3].get_width(),0))
    mr_dl = 'MixRamp delay: off'
    if 'mixrampdelay' in Status:
        if round(float(Status['mixrampdelay']),1) != 0.0:
            mr_dl = 'MixRamp delay: ' + str(round(float(Status['mixrampdelay']),1))+ 's'  
    draw_text(screen,mr_dl,status_font,font_color,align='centerx',pos=(0,chk_win[4].get_abs_offset()[1]))
    chk_win[4].blit(chk_buf[2],(0,0))
    chk_win[5].blit(chk_buf[3],(chk_win[5].get_width()-chk_buf[3].get_width(),0))
    draw_text(status_win,'Touch here for Basic Settings',status_font,status_color,align='centerx')

def set_xfade_state(idx=None):
# MixRamp benötigt MixRamp-Tags in den mp3-Dateien
# Fallback ist Crossfade, wenn die Tags nicht vorhanden sind
    global Refresh
    Status = mpc.status()
    if idx == 0:
        secs = 0
        if 'xfade' in Status:
            secs=int(Status['xfade'])-1
            if secs <= 0:
                secs = 0
        mpc.crossfade(secs)
    elif idx == 1:
        if 'xfade' in Status:
            secs=int(Status['xfade'])
            if secs > 14: secs = 14
        else: secs = 0
        mpc.crossfade(secs + 1)
    elif idx == 2:
        mr_db = float(Status['mixrampdb'])-0.5
        if mr_db < -30.0:
            mr_db = -30.0
        mpc.mixrampdb(mr_db)
    elif idx == 3:
        mr_db = float(Status['mixrampdb'])+0.5
        if mr_db > 0.0:
            mr_db = 0.0
        mpc.mixrampdb(mr_db)
    elif idx == 4:
        mr_dl = 'nan'
        if 'mixrampdelay' in Status:
            mr_dl = float(Status['mixrampdelay'])-0.5
            if mr_dl <= 0.0:
                mr_dl = 'nan'
        mpc.mixrampdelay(mr_dl)
    elif idx == 5:
        mr_dl = 0.5
        if 'mixrampdelay' in Status:
            mr_dl = float(Status['mixrampdelay'])+0.5
            if mr_dl > 15.0:
                mr_dl = 15.0
        mpc.mixrampdelay(mr_dl)
    else:
        return
    Refresh = True

def get_playback_state():
    draw_text(msg_win,'MPD Playback Settings',status_font,status_color,align='centerx')
    Status = mpc.status()
    if Status['repeat'] == '1':
        chk_win[0].blit(chk_buf[1],(0,0))
    else:
        chk_win[0].blit(chk_buf[0],(0,0))
    draw_text(chk_win[0],' Repeat',status_font,font_color,pos=(chk_buf[0].get_width(),0))
    if Status['random'] == '1':
        chk_win[1].blit(chk_buf[1],(0,0))
    else:
        chk_win[1].blit(chk_buf[0],(0,0))
    draw_text(chk_win[1],' Random',status_font,font_color,pos=(chk_buf[0].get_width(),0))
    if Status['consume'] == '1':
        chk_win[2].blit(chk_buf[1],(0,0))
    else:
        chk_win[2].blit(chk_buf[0],(0,0))
    draw_text(chk_win[2],' Consume',status_font,font_color,pos=(chk_buf[0].get_width(),0))
    if Status['single'] == '1':
        chk_win[3].blit(chk_buf[1],(0,0))
    else:
        chk_win[3].blit(chk_buf[0],(0,0))
    draw_text(chk_win[3],' Single',status_font,font_color,pos=(chk_buf[0].get_width(),0))
    draw_text(screen,'Replay-Gain:  ' + mpc.replay_gain_status(),status_font,font_color,align='centerx',pos=(0,chk_win[4].get_abs_offset()[1]))
    draw_text(status_win,'Touch here for X-Fade Settings',status_font,status_color,align='centerx')

def set_playback_state(idx=None):
    global Refresh
    Status = mpc.status()
    if idx == 0:
        mpc.repeat(int(Status['repeat'])^1)
    elif idx == 1:
        mpc.random(int(Status['random'])^1)
    elif idx == 2:
        mpc.consume(int(Status['consume'])^1)
    elif idx == 3:
        mpc.single(int(Status['single'])^1)
    elif idx == 4 or idx == 5:
        rg_mode = [ 'off' , 'track' , 'album' , 'auto' ]
        idx = rg_mode.index(mpc.replay_gain_status()) + 1
        if idx >= len(rg_mode):
            idx = 0
        mpc.replay_gain_mode(rg_mode[idx])
    else:
        return
    Refresh = True

def get_outputs():
    try:
        outputs = mpc.outputs()
    except:
        mpd_connect(mpc)
        outputs = mpc.outputs()
    n = len(outputs)
    if n > 6: n = 6
    for i in range(n):
        if outputs[i]['outputenabled'] == '1':
            chk_win[i].blit(chk_buf[1],(0,0))
        else:
            chk_win[i].blit(chk_buf[0],(0,0))
        draw_text(chk_win[i],' ' + outputs[i]['outputname'],status_font,font_color,pos=(chk_buf[0].get_width(),0))

def set_outputs(idx=None):
    global Refresh
    try:
        outputs = mpc.outputs()
    except:
        mpd_connect(mpc)
        outputs = mpc.outputs()
    n = len(outputs)
    if idx != None and idx < n:
        if outputs[idx]['outputenabled'] == '1':
            mpc.disableoutput(idx)
        else:
            mpc.enableoutput(idx)
            mpc.play()
        Refresh = True

def setvol(vol):
    if mpc.status()['volume'] != '-1':
        mpc.setvol(vol)

def button(number): #which button (and which menu) was pressed on touch
        global menu, screensaver,screensaver_timer
        global TenMins
        global skin_idx
        global font_color, skin_color
        global status_update_flag, oldvol
        global btn_update_flag, muted
        global playlists, pl_index

        global Dirty, pb_page
        global Refresh
        Refresh = False
        btn_update_flag = False
        status_update_flag = False

        try:
            Status = mpc.status()
            Info = mpc.currentsong()
        except mpd.CommandError:
            return

        if menu == 1: # Main Screen
            if number == 0: # msg_win
                if x_button and x_rect.collidepoint(pos):
                    if 'pos' in mpc.currentsong():
                        mpc.delete(int(mpc.currentsong()['pos']))
                else:
                    menu = 2
                    Refresh = True
                    Dirty = True
            elif number == 1: # stop/play
                if Status['state'] == 'stop':
                    mpc.play()
                else:
                    mpc.stop()
                btn_update_flag = True
            elif number == 2: # pause/play
                mpc.pause()
                btn_update_flag = True
            elif number == 3: # vol up
                vol = int(Status['volume'])
                if vol >= 95:
                    setvol(100)
                else:
                    setvol((vol + 5))
                if muted:
                    muted = False
                    btn_update_flag = True
                status_update_flag = True
            elif number == 4: #mute/unmute
                vol = int(Status['volume'])
                if vol != 0:
                    oldvol = vol
                    setvol(0)
                    muted = True
                else:
                    setvol(oldvol)
                    muted = False
                status_update_flag = True
                btn_update_flag = True
            elif number == 5: #prev
                Dirty = True
                btn_update_flag = True
                try:
                    if int(Info['pos'])+1 > 1:
                        mpc.previous()
                    else:
                        mpc.play(int(Status['playlistlength'])-1)
                except mpd.CommandError: pass
            elif number == 6: #next
                Dirty = True
                btn_update_flag = True
                try:
                    if int(Info['pos'])+1 < int(Status['playlistlength']):
                        mpc.next()
                    else:
                        mpc.play(0)
                except mpd.CommandError: pass
            elif number == 7: #vol down
                vol = int(Status['volume'])
                if vol <= 5:
                    setvol(0)
                    muted = True
                    btn_update_flag = True
                else:
                    setvol((vol - 5))
                status_update_flag = True
            elif number == 8: #next page
                # Gehe zum menu 3
                menu = 3
                Refresh = True
        elif menu == 2: # File Selection Screen
            Refresh = True
            Dirty = True
            if number == 0: # selection_win
                if plus_button and x_rect.collidepoint(pos):
                    if playlists[pl_index][0] == 'd':
                        waiting('adding Directory to Playlist')
                        mpc.add(playlists[pl_index][1])
                        pygame.time.wait(1500)
                        event=pygame.event.get() # werfe aufgelaufene Events weg
                menu = 1
                update_screen()
            elif number == 3: # up
                pl_index -= 1
                if pl_index < 0:
                    pl_index = len(playlists)-1
            elif number == 4: # updir
                old_dir = os.path.dirname(playlists[pl_index][1])
                up_dir = os.path.dirname(old_dir)
                playlists = get_playlists(up_dir)
                pl_index = 0
                for i in range(len(playlists)):
                    if playlists[i][1] == old_dir:
                         pl_index = i
            elif number == 7: # down
                pl_index += 1
                if pl_index >= len(playlists):
                    pl_index %= len(playlists)
            elif number == 8: # return
                if set_playlist(pl_index):
                    menu = 1
                else:
                    pl_index = 0
        elif menu == 3: # MPD Playback Settings Screen
            Refresh = True
            if number == 0:
                idx=-1
                for i in range(len(chk_rect)):
                    if chk_rect[i].collidepoint(pos): idx=i
                if idx > -1:
                    if pb_page: set_xfade_state(idx)
                    else: set_playback_state(idx)
                if status_rect.collidepoint(pos):
                    pb_page ^= 1
            elif number == 1:
                waiting('updating mpd-Database...')
                try: mpc.update()
                except: pass
                pygame.time.wait(2500)
                event=pygame.event.get() # werfe aufgelaufene Events weg
            elif number == 2:
                mpc.clear()
                waiting('cleared Playlist!')
                pygame.time.wait(1500)
                event=pygame.event.get() # werfe aufgelaufene Events weg
                Dirty = True
                menu = 2
            elif number == 3:
                waiting('saved Playlist as','\'' + save_filename + '\'')
                try: mpc.rm(save_filename)
                except: pass
                mpc.save(save_filename)
                pygame.time.wait(1500)
                event=pygame.event.get() # werfe aufgelaufene Events weg
            elif number == 4:
                waiting('shuffling Playlist...')
                mpc.shuffle()
                pygame.time.wait(1500)
                event=pygame.event.get() # werfe aufgelaufene Events weg
            elif number == 5:
                Dirty = True
                menu = 1
            elif number == 8:
                menu = 4
        elif menu == 4: # MPD audio_outputs Screen
            Refresh = True
            # mpd audio_outputs menu
            if number == 0:
                idx=-1
                for i in range(len(chk_rect)):
                    if chk_rect[i].collidepoint(pos): idx=i
                if idx > -1: set_outputs(idx)
            elif number == 1:
                TenMins = True
                menu = 6
            elif number == 2:
                menu = 5
            elif number == 3:
                # Neustart
                reboot()
            elif number == 4:
                # Ausschalten
                poweroff()
            elif number == 5:
                menu = 3
            elif number == 8:
                # Gehe zum menu 1
                menu = 1
                # Dirty Hack - Erzwinge update von Station und Titel
                Dirty = True
        elif menu == 5: # NewTron-Radio Settings Screen
            Refresh = True
            if number == 0:
                idx=-1
                if status_rect.collidepoint(pos):
                    idx = 9
                for i in range(len(chk_rect)):
                    if chk_rect[i].collidepoint(pos): idx=i
                if idx > -1: set_config(idx)
            if number == 1:
                waiting('saving configuration...')
                save_config()
                pygame.time.wait(1500)
                event=pygame.event.get() # werfe aufgelaufene Events weg
            elif number == 2:
                #print "switch skin"
                skin_idx += 1
                if skin_idx >= len(skins):
                    skin_idx = 0
                waiting("changing skin...")
                pygame.time.wait(1500)
                if enable_gpio:
                    GPIO.cleanup()
                pygame.quit()
                os.execl(sys.argv[0],sys.argv[0],skins[skin_idx])
            elif number == 3:
                # Auffrischen
                waiting("refreshing...")
                pygame.time.wait(1500)
                if enable_gpio:
                    GPIO.cleanup()
                pygame.quit()
                os.execl(sys.argv[0],sys.argv[0])
            elif number == 4:
                screensaver_timer+=1
                if screensaver_timer > 120:
                    screensaver_timer = 120
            elif number == 5:
                menu = 4
            elif number == 6:
                # Oberfläche beenden
                pygame.quit()
                sys.exit()
            elif number == 7:
                # Stop Radio und beende Oberfläche
                mpc.stop()
                pygame.quit()
                sys.exit()
            elif number == 8:
                screensaver_timer-=1
                if screensaver_timer <= 0:
                    screensaver_timer = 1
        elif menu == 6: # Weather Screen
            Refresh = True
            menu = 4

def pygame_svg(svg_file, color, size):
    with open(svg_file, "r+") as f:
        svgbuf = f.read()
    colorstr = '#%02x%02x%02x' % color
    svgbuf = svgbuf.replace("#00ffff", colorstr)

    svg = imlib2.open_from_memory(svgbuf,size)
    strbuf = str(svg.get_raw_data(format='RGBA'))
    image = pygame.image.frombuffer(strbuf, size,"RGBA").convert_alpha()
    return image

def skin2_base():
    screen.blit(btn_buf[3],btn_pos[3])      # up
    screen.blit(btn_buf[21],btn_pos[4])     # updir
    screen.blit(btn_buf[7],btn_pos[7])      # down
    screen.blit(btn_buf[20],btn_pos[8])     # enter
    screen.blit(sel_msg_buf,btn_pos[1])     # 'Select Music'-Text
    screen.blit(sel_buf,btn_pos[0])         # selection_frame

def skin3_base():
    screen.blit(btn_buf[0],btn_pos[0])      # msg_frame
    screen.blit(btn_buf[15],btn_pos[1])     # refresh
    screen.blit(btn_buf[23],btn_pos[2])     # trash
    screen.blit(btn_buf[24],btn_pos[3])     # save
    screen.blit(btn_buf[25],btn_pos[4])     # shuffle
    screen.blit(btn_buf[22],btn_pos[5])     # prev_page
    screen.blit(btn_buf[8],btn_pos[8])      # next_page

def skin4_base():
    screen.blit(btn_buf[0],btn_pos[0])      # msg_frame
    screen.blit(btn_buf[9],btn_pos[1])     # cloud (show_weather)
    screen.blit(btn_buf[26],btn_pos[2])    # config
    screen.blit(btn_buf[14],btn_pos[3])    # reboot
    screen.blit(btn_buf[13],btn_pos[4])    # poweroff
    screen.blit(btn_buf[22],btn_pos[5])    # prev_page
    screen.blit(btn_buf[8],btn_pos[8])     # next_page

def skin5_base():
    screen.blit(btn_buf[0],btn_pos[0])      # msg_frame
    screen.blit(btn_buf[24],btn_pos[1])     # save
    screen.blit(btn_buf[10],btn_pos[2])     # color (change_skin)
    screen.blit(btn_buf[15],btn_pos[3])     # refresh (restart radio)
    screen.blit(btn_buf[3],btn_pos[4])      # up
    screen.blit(btn_buf[22],btn_pos[5])     # prev_page
    screen.blit(btn_buf[11],btn_pos[6])     # exit (quit radio)
    screen.blit(btn_buf[12],btn_pos[7])     # quit (quit radio & mpd)
    screen.blit(btn_buf[7],btn_pos[8])      # down

def load_skin():
    global btn_buf, chk_buf, sel_buf, sel_msg_buf, wlan_buf
    global list_bg, station_bg, title_bg, status_bg, bitrate_bg
    global bg_buf, weather_bg_buf
    # Buttons laden
    btn_buf = [pygame_svg(os.path.join(SkinPath,msg_frame), skin_color, (w,h/2))]
    for i in range(len(btn_list)):
        btn_buf.append(pygame_svg(os.path.join(SkinPath,btn_list[i]),skin_color, (w/4,h/4)))
    chk_buf = []
    for i in range(len(chk_list)):
        chk_buf.append(pygame_svg(os.path.join(SkinPath,chk_list[i]),font_color,(msg_win.get_height()/5,msg_win.get_height()/5)))
    sel_buf = pygame_svg(os.path.join(SkinPath,selection_frame),skin_color,(w,h/2))
    sel_msg_buf = pygame_svg(os.path.join(SkinPath,select_pl),skin_color,(w/2,h/2))
    wlan_buf =[]
    for i in range(len(wlan_list)):
        wlan_buf.append(pygame_svg(os.path.join(SkinPath,wlan_list[i]),status_color,(status_font.get_height()*5/4,status_font.get_height())))

    # Hintergrundbilder laden
    if wallpaper:
        bg_buf = pygame.image.load(wallpaper).convert()
        bg_buf = pygame.transform.scale(bg_buf,size)
    else: bg_buf = None
    if weather_wallpaper:
        weather_bg_buf = pygame.image.load(weather_wallpaper).convert()
        weather_bg_buf = pygame.transform.scale(weather_bg_buf,size)
    else: weather_bg_buf = None

    # Hintergrund für screen.update(dirty_rects) erzeugen
    screen.fill(bg_color)
    if bg_buf:
        screen.blit(bg_buf,(0,0))
    if text_on_top:
        screen.blit(sel_buf, btn_pos[0]) # selection_frame
    list_bg = list_win[0].copy()
    screen.fill(bg_color)
    if bg_buf:
        screen.blit(bg_buf,(0,0))
    if text_on_top:
        screen.blit(btn_buf[0], btn_pos[0]) # skin surface
    station_bg = station_win.copy()
    title_bg = title_win.copy()
    status_bg = status_win.copy()
    bitrate_bg = bitrate_win.copy()

    event=pygame.event.get() # werfe aufgelaufene Events weg

def get_wlan_level(netdev):
    level = 0
    with open('/proc/net/wireless') as f:
        for line in f:
            wlan = line.split()
            if wlan[0] == netdev + ':':
                value = float(wlan[3])
                if value < 0:
                    # Näherungsweise Umrechnung von dBm in %
                    # -35dBm -> 100, -95dBm -> 0
                    level = int((value + 95)/0.6)
                else:
                    level = int(value)
    return level

def get_Station(Info):
    # Welcher Sender
    try: Station = Info['album']
    except: Station = None
    if not Station:
        try: Station = Info['name']
        except: Station = "no data"
    return Station

def get_Title(Info):
    # Welcher Titel
    try:
        Title = Info['title'].strip()
        # mit Spezialbehandlung für diverse Sender,
        # die vor den Songtitel nochmal den Sendernamen klatschen:
        if Station.upper().split()[-1][-3:]+': ' in Title.upper():
            m = re.search('(.*): (.*)', Title)
            Title = m.group(2)
        # Spezialbehandlung für diverse Icecast-Radiostationen
        if 'text=' in Title:
            m = re.search('(.*)text="([^"]*)"', Title)
            Title = m.group(1)+m.group(2)
    except: Title = "no data"
    try:
        Artist = Info['artist'].strip()
        if Artist == '': Artist = None
    except: Artist = None
    if Artist:
        Title = Artist + ' - ' + Title
    return Title

def show_weather(OWM_ID,OWM_KEY):
    Stadt = 'n/a'
    Temperatur = '-'
    Luftdruck = '-'
    Luftfeuchte = '-'
    Wetterlage = 'na'
    Heute_min = '-'
    Heute_max = '-'
    Morgen_min = '-'
    Morgen_max ='-'
    Vorschau = 'na'

    if not OWM_KEY:
        waiting('Please get an API-Key from','openweathermap.org/appid')
        pygame.time.wait(5000)
        event=pygame.event.get() # werfe aufgelaufene Events weg

    OpenWeather_Base = 'http://api.openweathermap.org/data/2.5/'
    try:
        weather = urllib2.urlopen(OpenWeather_Base + 'weather?id=' + OWM_ID + '&units=metric&lang=de&mode=json&APPID='+ OWM_KEY)
        weather_data = json.load(weather)
        Stadt = weather_data['name']
        Temperatur = str(int(round(weather_data['main']['temp'],0))) #  - 273.15 if units!=metric
        Luftdruck = str(int(weather_data['main']['pressure']))
        Luftfeuchte = str(int(weather_data['main']['humidity']))
        Wetterlage = weather_data['weather'][0]['icon']
    except:
        print datetime.datetime.now().strftime('%H:%M') + ': No Weather Data.'

    try:
        pygame.time.wait(150) # Warte 150ms um HttpError 429 zu vermeiden
        daily = urllib2.urlopen(OpenWeather_Base + 'forecast/daily?id=' + OWM_ID + '&units=metric&lang=de&mode=json&APPID='+ OWM_KEY)
        daily_data = json.load(daily)
        Heute_min = str(round(daily_data['list'][0]['temp']['min'],1))
        Heute_max = str(round(daily_data['list'][0]['temp']['max'],1))
        Morgen_min = str(round(daily_data['list'][1]['temp']['min'],1))
        Morgen_max = str(round(daily_data['list'][1]['temp']['max'],1))
        Vorschau = daily_data['list'][1]['weather'][0]['icon']
    except:
        print datetime.datetime.now().strftime('%H:%M') + ': No Forecast Data.'

    ss_weather_win.fill(weather_bg_color)
    if weather_bg_buf:
        ss_weather_win.blit(weather_bg_buf,(0,0),area=ss_weather_rect)
    fc_height = title_font.get_height()/4
    draw_text(screen,u'Wetter für ' + Stadt,title_font,weather_font_color,align='centerx',pos=(0,fc_height))
    fc_height = title_font.get_height()*5/4
    draw_text(screen,'Jetzt: ' + Temperatur + u'°C' + ' / ' + Luftdruck + 'mb' + ' / ' + Luftfeuchte + '%rel.',title_font,weather_font_color,align='centerx',pos=(0,fc_height))
    fc_height = fc_height + title_font.get_height()
    draw_text(screen,'Heute',status_font,weather_font_color,align='centerx',pos=(-ss_weather_win.get_width()/4,fc_height))
    draw_text(screen,'Morgen',status_font,weather_font_color,align='centerx',pos=(ss_weather_win.get_width()/4,fc_height))

    icon = os.path.join(WeatherPath,Wetterlage+'.png')
    if not os.path.exists(icon):
        icon = os.path.join(WeatherPath,'na.png')
    icon2 = os.path.join(WeatherPath,Vorschau+'.png')
    if not os.path.exists(icon2):
        icon2 = os.path.join(WeatherPath,'na.png')
    icon = pygame.image.load(icon).convert_alpha()
    icon2 = pygame.image.load(icon2).convert_alpha()
    icon = pygame.transform.smoothscale(icon,(ss_weather_win.get_height()*8/16, ss_weather_win.get_height()*8/16))
    icon2 = pygame.transform.smoothscale(icon2,(ss_weather_win.get_height()*8/16, ss_weather_win.get_height()*8/16))
    fc_height = fc_height + status_font.get_height()
    screen.blit(icon, (ss_weather_win.get_width()/4 - icon.get_width()/2, fc_height))
    screen.blit(icon2, (ss_weather_win.get_width()*3/4 - icon.get_width()/2, fc_height))

    fc_height = fc_height + icon.get_height()
    heute_text=Heute_min + '/' + Heute_max + u'°C'
    draw_text(screen,heute_text,status_font,weather_font_color,align='centerx',pos=(-ss_weather_win.get_width()/4,fc_height))
    morgen_text=Morgen_min + '/' + Morgen_max + u'°C'
    draw_text(screen,morgen_text,status_font,weather_font_color,align='centerx',pos=(ss_weather_win.get_width()/4,fc_height))
    pygame.display.update(ss_weather_rect)

def show_ss_status(show_clock=True):
    global Station
    Info = mpc.currentsong()
    Station = get_Station(Info) # wird für get_Title() benötigt
    ss_title = get_Title(Info)
    # Wenn der Titel zu lang ist, kürzen und mit '...' ergänzen
    if status_font.size(ss_title)[0] > ss_title_win.get_width():
        while status_font.size(ss_title)[0] > ss_title_win.get_width():
            ss_title = ss_title[:-1]
        ss_title = ss_title[:-3]+'...'
    draw_text(ss_title_win,ss_title,status_font,status_color,align='centerx')
    if show_clock:
        ss_clock = datetime.datetime.now().strftime('%H:%M')
        draw_text(ss_clock_win,ss_clock,title_font,status_color,align='centerx')
        pygame.display.update([ss_title_rect,ss_clock_rect])
    else:
        pygame.display.update(ss_title_rect)

class ScrollText(object):
    """
    Einfacher Lauftext
    Modified version of https://github.com/gunny26/pygame/blob/master/ScrollText.py
    """
    def __init__(self, surface, text, font, color, bg, skin_buf):
        """
        (pygame.Surface) surface - surface to draw on
        (string) text - text to draw
        (int) hpos - horizontal position on y axis
        (pygame.font.Font) - font to use
        (pygame.Color) color - color of font
        (pygame.Surface.copy) bg - copy of surface background
        """
        self.surface = surface
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()
        self.text = text
        self.color = color
        self.font = font
        self.bg = bg
        self.skin_buf = skin_buf
        self.rflag = True
        # initialize
        self.position = 0
        self.oldpos = -1
        self.font = font
        self.rect = self.surface.get_rect(topleft=self.surface.get_abs_offset())
        self.surface.set_colorkey((127,127,127))
        self.surface.fill((127,127,127))
        if dropshadow:
            self.text_shadow=self.font.render(self.text, True, shadow_color).convert_alpha()
        self.text_surface = self.font.render(self.text, True, self.color).convert_alpha()
        self.text_width = self.text_surface.get_width()

    def update(self):
        """update every frame"""
        if self.oldpos != self.position:
            self.surface.blit(self.bg,(0,0))
            if dropshadow:
                self.surface.blit(self.text_shadow,
                    (1, 1),
                    (self.position, 0, self.width, self.height)
                )
            self.surface.blit(self.text_surface,
                (0, 0),
                (self.position, 0, self.width, self.height)
            )
            self.oldpos = self.position
            if not text_on_top:
                screen.blit(self.skin_buf,self.rect,area=self.rect)
            pygame.display.update(self.rect)
        if ((self.text_width - self.position) >= self.width) and (self.rflag == True):
            self.position += 1
        else:
            self.rflag = False
        if (self.position > 0) and (self.rflag == False):
            self.position -= 1
        else:
            self.rflag = True

def update_screen(): #Hauptfunktion

    global _station_label
    global _title_label
    global _select_label
    global Station
    global Title
    global screensaver

    global FiveSecs, OneSec
    global TenMins, minutes
    global Refresh
    global status_update_flag
    global btn_update_flag
    global Dirty, pb_page

    if not screensaver:


        if menu == 1: # Main Screen

            Info = mpc.currentsong()

            # ScrollText nur Aktualisieren, wenn sich der Stationsname geändert hat
            _old_Station = Station
            Station = get_Station(Info)
            if Dirty or (Station != _old_Station):
                _station_label = ScrollText(station_win,Station,status_font,status_color,station_bg,btn_buf[0])
                btn_update_flag = True

            # ScrollText nur Aktualisieren, wenn sich der Titel geändert hat
            _old_Title = Title
            Title = get_Title(Info)
            if Dirty or (Title != _old_Title):
                _title_label = ScrollText(title_win, Title, title_font, (font_color),title_bg,btn_buf[0])
                btn_update_flag = True

            Dirty = False

            if Refresh:
                screen.fill(bg_color)
                if bg_buf:
                    screen.blit(bg_buf,(0,0),area=btn_rect[0])
                if text_on_top:
                    screen.blit(btn_buf[0], btn_pos[0]) # msg_frame
                draw_text(msg_win,'Now playing:',font,font_color,pos=(0,title_win.get_offset()[1]-font.get_height()))
                if x_button and ('pos' in Info):
                    pygame.draw.rect(x_win, (font_color), x_win.get_rect(),x_win.get_width()/7)
                    pygame.draw.line(x_win, (font_color), (x_win.get_width()/4,x_win.get_height()/4), (x_win.get_width()*3/4,x_win.get_height()*3/4),x_win.get_width()/8)
                    pygame.draw.line(x_win, (font_color), (x_win.get_width()/4,x_win.get_height()*3/4), (x_win.get_width()*3/4,x_win.get_height()/4),x_win.get_width()/8)
                btn_update_flag = True
                status_update_flag = True

            if btn_update_flag:
                Status = mpc.status()
                btn_update_flag = False
                screen.fill(bg_color,btn_rect[9])
                if bg_buf:
                    screen.blit(bg_buf,btn_rect[9],area=btn_rect[9])
                if 'state' in Status:
                    if (Status['state'] == 'stop'):
                        screen.blit(btn_buf[16], btn_pos[1]) # play
                        screen.blit(btn_buf[18], btn_pos[2]) # empty
                    elif (Status['state'] == 'pause'):
                        screen.blit(btn_buf[1], btn_pos[1])  # stop
                        screen.blit(btn_buf[16], btn_pos[2]) # play
                    else:
                        screen.blit(btn_buf[1], btn_pos[1])  # stop
                        screen.blit(btn_buf[2], btn_pos[2])  # pause
                    if muted:
                        screen.blit(btn_buf[17], btn_pos[4]) # unmute
                    else:
                        screen.blit(btn_buf[4], btn_pos[4])  # mute

                screen.blit(btn_buf[3],btn_pos[3])  # vol_up
                screen.blit(btn_buf[5],btn_pos[5])  # prev
                screen.blit(btn_buf[6],btn_pos[6])  # next
                screen.blit(btn_buf[7],btn_pos[7])  # vol_down
                screen.blit(btn_buf[8],btn_pos[8])  # next_page
                pygame.display.update(btn_rect[9])

            if OneSec:
                OneSec = False
                status_update_flag = True

            if status_update_flag:
                status_update_flag = False
                status_win.blit(status_bg,(0,0))
                bitrate_win.blit(bitrate_bg,(0,0))
                status_update(Info)
                if not text_on_top:
                    if Refresh:
                        screen.blit(btn_buf[0], btn_pos[0]) # msg_frame
                    else:
                        screen.blit(btn_buf[0],status_rect,area=status_rect)
                        screen.blit(btn_buf[0],bitrate_rect,area=bitrate_rect)
                if Refresh:
                    pygame.display.update(btn_rect[0])
                    Refresh = False
                else:
                    pygame.display.update([bitrate_rect,status_rect])

            _station_label.update()
            _title_label.update()

        elif menu == 2: # Playlist Selection
            if FiveSecs:
                FiveSecs = False
                Refresh = True
                
            if Refresh:
                Refresh = False
                screen.fill(bg_color)
                if bg_buf:
                    screen.blit(bg_buf,(0,0))
                if text_on_top:
                    skin2_base()
                show_playlists(pl_index)
                if Dirty:
                    _select_label = ScrollText(list_win[0], playlists[pl_index][1].split('/')[-1].replace('.m3u','',1),title_font,playlists[pl_index][2],list_bg,sel_buf)
                if plus_button:
                    if playlists[pl_index][0] == 'd':
                        pygame.draw.rect(x_win, (font_color), x_win.get_rect(),x_win.get_width()/7)
                        pygame.draw.line(x_win, (font_color), (x_win.get_width()/2,x_win.get_height()/4), (x_win.get_width()/2,x_win.get_height()*3/4),x_win.get_width()/8)
                        pygame.draw.line(x_win, (font_color), (x_win.get_width()/4,x_win.get_height()/2), (x_win.get_width()*3/4,x_win.get_height()/2),x_win.get_width()/8)
                if not text_on_top:
                    skin2_base()
                if Dirty:
                    pygame.display.flip()
                    Dirty = False
            _select_label.update()

        elif menu == 3: # MPD Playback Settings
            if FiveSecs:
                FiveSecs = False
                Refresh = True

            if Refresh:
                Refresh = False
                screen.fill(bg_color)
                if bg_buf:
                    screen.blit(bg_buf,(0,0))
                if text_on_top:
                    skin3_base()
                if pb_page: get_xfade_state()
                else: get_playback_state()
                if not text_on_top:
                    skin3_base()
                pygame.display.flip()

        elif menu == 4: # MPD Audio Outputs


            # Mindestens alle 5 Sekunden Aktualisieren
            if FiveSecs:
                FiveSecs = False
                Refresh = True

            if Refresh:
                Refresh = False
                screen.fill(bg_color)
                if bg_buf:
                    screen.blit(bg_buf,(0,0))
                if text_on_top:
                    skin4_base()
                draw_text(msg_win,'MPD Audio Outputs',status_font,status_color,align='centerx')
                get_outputs()
                current_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
                draw_text(status_win,current_time,status_font,status_color)

                #get and display ip
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(('8.8.8.8', 0)) # dummy IP
                    ip_text='IP: ' + s.getsockname()[0]
                    s.close()
                except:
                    ip_text='IP: No Network!'
                #Wlan Level
                wlanlevel=get_wlan_level(wlan_device)
                if wlanlevel >= 80:
                    status_win.blit(wlan_buf[4],(status_win.get_width()/2-wlan_buf[4].get_width()/2,0))
                elif wlanlevel >= 55:
                    status_win.blit(wlan_buf[3],(status_win.get_width()/2-wlan_buf[3].get_width()/2,0))
                elif wlanlevel >= 30:
                    status_win.blit(wlan_buf[2],(status_win.get_width()/2-wlan_buf[2].get_width()/2,0))
                elif wlanlevel >= 5:
                    status_win.blit(wlan_buf[1],(status_win.get_width()/2-wlan_buf[1].get_width()/2,0))
                else:
                    status_win.blit(wlan_buf[0],(status_win.get_width()/2-wlan_buf[0].get_width()/2,0))
                draw_text(status_win,ip_text,status_font,status_color,align='topright')
                if not text_on_top:
                    skin4_base()
                pygame.display.flip()

        elif menu == 5: # NewTron-Radio Settings
            if Refresh:
                Refresh = False
                screen.fill(bg_color)
                if bg_buf:
                    screen.blit(bg_buf,(0,0))
                if text_on_top:
                    skin5_base()
                get_config()
                if not text_on_top:
                    skin5_base()
                pygame.display.flip()

        elif menu == 6: # Weather Screen
            if TenMins or Refresh:
                show_weather(OWM_ID,OWM_KEY)
                TenMins = False
            if FiveSecs or Refresh:
                FiveSecs = False
                Refresh = False
                ss_title_win.fill(weather_bg_color)
                ss_clock_win.fill(weather_bg_color)
                if weather_bg_buf:
                    ss_title_win.blit(weather_bg_buf,(0,0),area=ss_title_rect)
                    ss_clock_win.blit(weather_bg_buf,(0,0),area=ss_clock_rect)
                show_ss_status()

    else:  #screensaver == True:
        if screensaver_mode == 'weather':
            if (minutes >= screensaver_timer) or TenMins:
                minutes = 0
                TenMins = False
                show_weather(OWM_ID,OWM_KEY)
            if FiveSecs or Refresh:
                FiveSecs = False
                Refresh = False
                ss_title_win.fill(weather_bg_color)
                ss_clock_win.fill(weather_bg_color)
                if weather_bg_buf:
                    ss_title_win.blit(weather_bg_buf,(0,0),area=ss_title_rect)
                    ss_clock_win.blit(weather_bg_buf,(0,0),area=ss_clock_rect)
                show_ss_status()

        elif screensaver_mode == 'clock':
            if FiveSecs or Refresh:
                FiveSecs = False
                Refresh = False
                screen.fill(bg_color)
                clock = datetime.datetime.now().strftime('%H:%M')
                clock_label = clock_font.render(clock,1,clock_font_color,bg_color)
                screen.blit(clock_label,
                    (   randint(0,w - clock_label.get_width()),
                        randint(0,h - ss_title_win.get_height() - clock_label.get_height())
                    )
                )
                show_ss_status(show_clock=False)
                pygame.display.flip()
        elif screensaver_mode == 'black':
            if TenMins or Refresh:
                TenMins = False
                Refresh = False
                if enable_gpio:
                    GPIO.output(18, bl_off)
                screen.fill(bg_color)
                pygame.display.flip()
        else:
            screensaver = False

##### Ende der Funktions- und Klassendefinitionen ##########

# Lese Konfigurationsdaten
read_config()
disp_init()
pygame.font.init()
print('Display area size: %d x %d' % size)
if (Fullscreen):
    screen = pygame.display.set_mode(size, pygame.SRCALPHA | pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode(size, pygame.SRCALPHA)

# Verbinde mit MPD
mpc = mpd.MPDClient(use_unicode=True)
mpc.timeout = 10
mpc.idletimeout = None
mpd_connect(mpc)
try: mpc.update()
except: pass
if 'volume' in mpc.status():
    if int(mpc.status()['volume']) < 5:
        setvol(oldvol)
else:
    try: setvol(oldvol)
    except: print "could not set volume - continuing anyway..."

# OpenWeatherMap Ortsdaten und Key
# Falls eine Umgebungsvariable 'OWM_ID' existiert, nehme diese
if os.getenv('OWM_ID'):
    OWM_ID=os.getenv('OWM_ID')
# Falls eine Umgebungsvariable 'OWM_KEY' existiert, nehme diese
if os.getenv('OWM_KEY'):
    OWM_KEY=os.getenv('OWM_KEY')

##### Skin management ######################################
try:
    skin=sys.argv[1]
    menu = 5
except: pass

# Pfad zu den Button und Imagedateien des Skins
SkinBase = os.path.join(ScriptPath,'skins')
SkinPath = os.path.join(SkinBase,skin)
WeatherPath = os.path.join(SkinBase,"weather")

read_skin_config()
skins=get_skins()
try:
    skin_idx=skins.index(skin)
except:
    print "Could not find a valid Skin!"
    print "exiting..."
    if enable_gpio:
        GPIO.cleanup()
    pygame.quit()
    sys.exit()

# Abstand des Textes von den Bildschirmrändern
# relativ zur Basisgrösse des Skins (480x320)
border_top = 14*h/320
border_side = 21*w/480

# Screensaver-rects
ss_title_win = screen.subsurface(
    [   0,
        h - status_font.get_height()*3/2,
        w,
        status_font.get_height()*3/2
    ]
)
ss_title_rect = ss_title_win.get_rect(topleft=ss_title_win.get_abs_offset())

ss_clock_win = screen.subsurface(
    [   0,
        ss_title_win.get_abs_offset()[1] - title_font.get_height(),
        w,
        title_font.get_height()
    ]
)
ss_clock_rect = ss_clock_win.get_rect(topleft=ss_clock_win.get_abs_offset())

ss_weather_win = screen.subsurface(
    [   0,
        0,
        w,
        ss_clock_win.get_abs_offset()[1]
    ]
)
ss_weather_rect = ss_weather_win.get_rect(topleft=ss_weather_win.get_offset())

# Fenster für alles innerhalb des msg_frames
msg_win = screen.subsurface(
    [   border_side,
        border_top,
        w - 2 * border_side,
        h/2 - 2*border_top
    ]
)

# Fenster für den Stationsnamen (left,top,width,height)
station_win = msg_win.subsurface(
    [   0,
        0,
        msg_win.get_width()*12/16,
        status_font.get_height()
    ]
)

# Fenster in dem der Titel eingeblendet wird (left,top,width,height)
title_win = msg_win.subsurface(
   [    0,
        msg_win.get_height()/2 - title_font.get_height() / 4,
        msg_win.get_width(),
        title_font.get_height()
    ]
)

# Fenster für die Statusinfos (left,top,width,height)
status_win = msg_win.subsurface(
    [   0,
        msg_win.get_height() - status_font.get_height(),
        msg_win.get_width(),
        status_font.get_height()
    ]
)
status_rect = status_win.get_rect(topleft=status_win.get_abs_offset())

#Fenster für die Anzeige der Bitrate (left,top,width,height)
bitrate_win = msg_win.subsurface(
    [   msg_win.get_width()*12/16,
        0,
        msg_win.get_width()*4/16,
        status_font.get_height()
    ]
)
bitrate_rect = bitrate_win.get_rect(topleft=bitrate_win.get_abs_offset())

x_win = msg_win.subsurface(
    [   title_win.get_width() - title_font.get_height(),
        bitrate_win.get_height(),
        title_font.get_height(),
        title_font.get_height(),
    ]
)
x_rect = x_win.get_rect(topleft=x_win.get_abs_offset())

# Bereiche für die Checkboxen
chk_win = [msg_win.subsurface(
        [   0,
            msg_win.get_height()*1/5,
            msg_win.get_width()/2,
            h/10
        ]
    ),
    msg_win.subsurface(
        [   msg_win.get_width()/2,
            msg_win.get_height()*1/5,
            msg_win.get_width()/2,
            h/10
        ]
    ),
    msg_win.subsurface(
        [   0,
            msg_win.get_height()*2/5,
            msg_win.get_width()/2,
            h/10
        ]
    ),
    msg_win.subsurface(
        [   msg_win.get_width()/2,
            msg_win.get_height()*2/5,
            msg_win.get_width()/2,
            h/10
        ]
    ),
    msg_win.subsurface(
        [   0,
            msg_win.get_height()*3/5,
            msg_win.get_width()/2,
            h/10
        ]
    ),
    msg_win.subsurface(
        [   msg_win.get_width()/2,
            msg_win.get_height()*3/5,
            msg_win.get_width()/2,
            h/10
        ]
    )
]
chk_rect = []
for i in range(len(chk_win)):
    chk_rect.append(chk_win[i].get_rect(topleft=chk_win[i].get_abs_offset()))

# Fenster für die Playlistenauswahl
list_win = [screen.subsurface(
        [   border_side,
            h/4 - title_font.get_height()/2,
            w - 2 * border_side,
            title_font.get_height()
        ]
    ),
    screen.subsurface(
        [   border_side,
            h/4 - title_font.get_height()/2 - status_font.get_height()*7/5,
            msg_win.get_width(),
            status_font.get_height()
        ]
    ),
    screen.subsurface(
        [   border_side,
            h/4 - title_font.get_height()/2 - status_font.get_height()*12/5,
            msg_win.get_width(),
            status_font.get_height()
        ]
    ),
    screen.subsurface(
        [   border_side,
            h/4 + title_font.get_height()/2 + status_font.get_height()*2/5,
            msg_win.get_width(),
            status_font.get_height()
        ]
    ),
    screen.subsurface(
        [   border_side,
            h/4 + title_font.get_height()/2 + status_font.get_height()*7/5,
            msg_win.get_width(),
            status_font.get_height()
        ]
    )
]

# Startbildschirm anzeigen
splashscreen = os.path.join(SkinBase,"Splash.png")
splash_buf = pygame.image.load(splashscreen).convert_alpha()
splash_buf = pygame.transform.smoothscale(splash_buf,size)
screen.blit(splash_buf,(0,0))
del splash_buf
pygame.display.flip()

btn_win = screen.subsurface([ 0,h/2,w,h/2 ])
# Touchbutton Positionen (screen)
btn_pos = [(0,0),(0,h/2),(w/4,h/2),(w/2,h/2),(w*3/4,h/2),
        (0,h*3/4),(w/4,h*3/4),(w/2,h*3/4),(w*3/4,h*3/4)]
# Obere Bildschirmhälfte (btn_rect[0]), der Bereich des Anzeigefensters
btn_rect=[pygame.Rect(0,0,w,h/2)]
# Rects der acht Buttons
for i in range(1,len(btn_pos)):
    btn_rect.append(pygame.Rect(btn_pos[i][0],btn_pos[i][1],w/4,h/4))
# Untere Bildschirmhälfte (btn_rect[9]), der Bereich der Buttons
btn_rect.append(btn_win.get_rect(topleft=btn_win.get_abs_offset()))

# Lade den Skin
load_skin()

# Hole Playlisten
init_playlists()
playlists = get_playlists()
pl_index = 0

#userevent on every minute, used for screensaver
pygame.time.set_timer(USEREVENT + 1, 60000)
#userevent on every second, used for screen-updates
pygame.time.set_timer(USEREVENT + 2, 1000)
#userevent on every 30 seconds, used for mpc.ping()
pygame.time.set_timer(USEREVENT + 3, 30000)
#userevent on every 10 minutes, used for Weather-Update
pygame.time.set_timer(USEREVENT + 4, 600000)
sclock = pygame.time.Clock()

###### Start der Anzeige ###################################

update_screen()

##### Start der Eventschleife ##############################

try:
    running = True
    while running:
        sclock.tick(FPS)
        for event in pygame.event.get():
            if event.type == USEREVENT + 1:
                minutes += 1
            if event.type == USEREVENT + 2:
                OneSec = True
                seconds += 1
                if seconds >= 5:
                    FiveSecs = True
                    seconds = 0
            if event.type == USEREVENT + 3:
                # try to keep connection to mpd alive
                try: mpc.ping()
                except:
                    mpd_connect(mpc)
            if event.type == USEREVENT + 4:
                TenMins = True
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            #if screensaver is enabled and the screen was touched,
            #just disable screensaver, reset timer and update screen
            #no button state will be checked
            try:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if screensaver:
                        Refresh = True
                        # Dirty Hack - Erzwinge update von Station und Titel
                        Dirty = True
                        minutes = 0
                        screensaver = False
                        if enable_gpio:
                            GPIO.output(18, bl_on)
                        if menu == 6 and screensaver_mode == 'weather': # Wetteranzeige über Wolkenbutton
                            menu = 4
                    else:
                        #if screen was touched and screensaver is
                        #disabled, get position of touched button,
                        #reset timer and call button()
                        pos = (pygame.mouse.get_pos() [0], pygame.mouse.get_pos() [1])
                        minutes = 0
                        for i in range(len(btn_rect)-1):
                            if btn_rect[i].collidepoint(pos):
                                button(i)
            except KeyError: pass
            except socket.timeout as e:
                print str(e) + "\nRestarting mpd..."
                subprocess.call("sudo service mpd restart", shell=True)
                Refresh = True
                Dirty = True
                pygame.time.wait(1500)
            except (mpd.ConnectionError, socket.error) as e:
                print('Connection Error (touch): ' + str(e))
                mpd_connect(mpc)
                Refresh = True
                Dirty = True

        #enable screensaver on timer overflow
        if minutes >= screensaver_timer:
            if screensaver_mode != 'off':
                screensaver = True
                if enable_gpio:
                    GPIO.output(18, bl_off)

        try:
            update_screen()
        except (mpd.ConnectionError, socket.error) as e:
            print('Connection Error (update): ' + str(e))
            mpd_connect(mpc)
            Refresh = True
            Dirty = True
        except mpd.CommandError as e:
            print 'CommandError (update): ' + str(e)
            waiting('one output required!')
            pygame.time.wait(5000)
            event=pygame.event.get() # werfe aufgelaufene Events weg
            menu = 3
            Refresh = True
except KeyboardInterrupt:
    # Clean exit if Ctrl-C was pressed
    print "\nCtrl-C pressed - exiting..."
    pygame.quit()
    sys.exit()
finally:
    if enable_gpio:
        GPIO.setwarnings(False)
        GPIO.output(18, bl_on)
        GPIO.cleanup()
    print "\nbye...\n"
