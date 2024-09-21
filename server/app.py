from flask import Flask, redirect, request, render_template
import requests as req
from threading import Thread
import time
from downloader.downloader import download_song
from gen_show import gen_show
from flask_socketio import SocketIO
import os
from pydub import AudioSegment
from analysis import generate_normalized_array
import colorextraction as ce
from PIL import Image, ImageDraw

import eventlet
from eventlet import wsgi

app = Flask(__name__)
app.config['SECRET_KEY'] = ''
socketio = SocketIO(app, cors_allowed_origins="*")



@app.route('/login')
def login():
    return redirect("https://accounts.spotify.com/authorize?client_id="+client_id+"&response_type=code&redirect_uri=http://localhost:3000/callback&scope=user-read-playback-state")

oauth = {}

@app.route('/callback')
def callback():
    res = req.post("https://accounts.spotify.com/api/token", data={
        "grant_type": "authorization_code",
        "code": request.args.get("code"),
        "redirect_uri": "http://localhost:3000/callback",
        "client_id": client_id,
        "client_secret": client_secret
    })
    if res.status_code != 200:
        return res.text
    global oauth
    oauth = res.json()
    return redirect("/")

currently_playing = {}

def get_playing():
    global oauth
    if "access_token" not in oauth:
        return
    res = req.get("https://api.spotify.com/v1/me/player", headers={
        "Authorization": "Bearer "+oauth["access_token"]
    })
    if res.status_code != 200:
        return
    return res.json()

def retrieve_song_art(song_id):
    img =  song_id+'.jpg'
    img = ce.Vibrant(img)
    img.generate_vibrant_pallete()
    hexcolors =    []  
    for i, c in enumerate(img.VibrantPallete):
        hexcolors.append(c.get_hex()) 
        rgbcolors = []
        for i in hexcolors:
            i = str(i).strip('#')
            tmp = []
            for j in (0, 2, 4):
                tmp.append((int(i[j:j+2], 16)))
        rgbcolors.append(tuple(tmp))
    return rgbcolors

    
    

def build_light_sequence():
    global currently_playing
    song_id = "temp_image"
    # colorlist = retrieve_song_art(song_id)
    song_id = currently_playing["item"]["id"]
    path = download_song(song_id, "./out")
   
    sound = AudioSegment.from_file(path, format="m4a")
    new_path = path.replace(".m4a", ".wav")
    sound.export(new_path, format="wav")

    interval = 50
    audio_frames = generate_normalized_array(new_path, interval)
    ls = gen_show(
         [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (139, 0, 255)],#rgbs
        audio_frames,
    )
    
    os.remove(path)
    os.remove(new_path)

    song_progress = int(get_playing()["progress_ms"])

    # Attempted sync & adjustment
    """ my_time = int(time.time() * 1000)
    spotify_ms = int(play_data["timestamp"])
    print("Song progress: " + str(song_progress))
    print("My time: " + str(my_time))
    print("Spotify time: " + str(spotify_ms))
    
    song_progress = my_time - spotify_ms + song_progress """
    print("Light show generated!")
    return {
        "progress_ms": song_progress,
        "sequence": ls,
        "frames": audio_frames,
        "interval": interval,
    }

def poll_playing():
    last_song = ""
    while True:
        try:
            global currently_playing
            currently_playing = get_playing()

            if currently_playing:
                song = currently_playing["item"]["id"]
                if song != last_song:
                    last_song = song
                    print("New song: " + song)
                    seq = build_light_sequence()
                    print("Emitting sequence...")
                    socketio.emit("new_sequence", seq)
        except Exception as e:
            print("Error polling playing: " + str(e))
        time.sleep(1)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/')
def index():
    global currently_playing
    return render_template("index.html", playing=currently_playing)

@app.route('/sim')
def sim():
    return render_template("sim.html")

if __name__ == '__main__':
    Thread(target=poll_playing, daemon=True).start()
    wsgi.server(eventlet.listen(("127.0.0.1", 3000)), app)