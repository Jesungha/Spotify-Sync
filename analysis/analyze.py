import matplotlib.pyplot as plt
from scipy.fftpack import fft
from scipy.io import wavfile # get the api
import os
import numpy as np
import plotly.graph_objects as go
import tqdm

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import time

from playsound import playsound
import threading

import termplotlib as tpl
import math

FPS = 30
FFT_WINDOW_SECONDS = 0.25

fs, data = wavfile.read("./sample.wav") # load the data
audio = data.T[0] # this is a two channel soundtrack, get the first track
FRAME_STEP = (fs / FPS) # audio samples per video frame
FFT_WINDOW_SIZE = int(fs * FFT_WINDOW_SECONDS) # seconds
AUDIO_LENGTH = len(audio)/fs # seconds

window = 0.5 * (1 - np.cos(np.linspace(0, 2*np.pi, FFT_WINDOW_SIZE, False)))

FRAME_COUNT = int(AUDIO_LENGTH*FPS) # frames
FRAME_OFFSET = int(len(audio)/FRAME_COUNT) # samples


def extract_sample(audio, frame_number):
  end = frame_number * FRAME_OFFSET
  begin = int(end - FFT_WINDOW_SIZE)

  if end == 0:
    # We have no audio yet, return all zeros (very beginning)
    return np.zeros((np.abs(begin)),dtype=float)
  elif begin<0:
    # We have some audio, padd with zeros
    return np.concatenate([np.zeros((np.abs(begin)),dtype=float),audio[0:end]])
  else:
    # Usually this happens, return the next sample
    return audio[begin:end]


FREQ_MIN = 10
FREQ_MAX = 1000

def plot_fft(p, xf, fs, dimensions=(960,540), y_max=1):
  layout = go.Layout(
      title="frequency spectrum",
      autosize=False,
      width=dimensions[0],
      height=dimensions[1],
      xaxis_title="Frequency (note)",
      yaxis_title="Magnitude",
      font={'size' : 24}
  )

  fig = go.Figure(layout=layout,
                  layout_xaxis_range=[FREQ_MIN,FREQ_MAX],
                  layout_yaxis_range=[0,y_max]
                  )
  
  fig.add_trace(go.Scatter(
      x = xf,
      y = p))
  
  return fig

mx = 0
for frame_number in range(FRAME_COUNT):
  sample = extract_sample(audio, frame_number)

  fft = np.fft.rfft(sample * window)
  fft = np.abs(fft).real 
  mx = max(np.max(fft),mx)

xf = np.fft.rfftfreq(FFT_WINDOW_SIZE, 1/fs)
RESOLUTION = (1920, 1080)


style.use('fivethirtyeight')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)

INTERVAL = 100

def animate(i):
    sample = extract_sample(audio, int(FPS*(i*INTERVAL/1000)))

    fft = np.fft.rfft(sample * window)
    fft = np.abs(fft) / mx
    
    ax1.clear()

    ax1.set_ylim(0,1)
    ax1.set_xlim(FREQ_MIN,FREQ_MAX)

    ax1.plot(xf, fft.real)

    fft = np.fft.rfft(sample * window)
    fft = np.abs(fft) / mx

def animate_bar(i):
    sample = extract_sample(audio, int(FPS*(i*INTERVAL/1000)))

    fft = np.fft.rfft(sample * window)
    fft = np.abs(fft) / mx
    
    ax1.clear()

    ax1.set_ylim(0,1)
    ax1.set_xlim(1,7)

    ax1.plot(xf, fft.real)

    fft = np.fft.rfft(sample * window)
    fft = np.abs(fft) / mx


WINDOW_INT_S = INTERVAL/1000
WINDOW_CNT = int(AUDIO_LENGTH/(WINDOW_INT_S))

mins = [math.inf]*7
maxs = [-math.inf]*7

for i in range(WINDOW_CNT):
  frame = int(FPS*(i*WINDOW_INT_S))
  sample = extract_sample(audio, frame)

  fft = np.fft.rfft(sample * window)
  fft = np.abs(fft) / mx

  x = xf
  y = fft.real

  x_split = np.array_split(x, 7)
  y_split = np.array_split(y, 7)
  y_new = [np.mean(y_split[i]) for i in range(7)]
  y = np.array(y_new)

  for j in range(7):
    if y_new[j] == 0:
      continue
    mins[j] = min(mins[j], y_new[j])
    maxs[j] = max(maxs[j], y_new[j])

def make_cli_chart(frame):
  sample = extract_sample(audio, frame)

  fft = np.fft.rfft(sample * window)
  fft = np.abs(fft) / mx

  x = xf
  y = fft.real

  x_split = np.array_split(x, 7)
  y_split = np.array_split(y, 7)
  y_new = [np.mean(y_split[i]) for i in range(7)]
  y = np.array(y_new)

  for j in range(7):
    n = np.abs(y_new[j] - mins[j])/(maxs[j] - mins[j])
    y_new[j] = n

  fig = tpl.figure()
  fig.barh(y_new, ["1", "2", "3", "4", "5", "6", "7"], force_ascii=True)
  fig.show()

threading.Thread(target=playsound, args=('/Users/aryan/dev/misc/spotify-rgb-sync/analysis/sample.wav',), daemon=True).start()

""" ani = animation.FuncAnimation(fig, animate, interval=INTERVAL)
plt.show() """

for i in range(WINDOW_CNT):
  make_cli_chart(int(FPS*(i*WINDOW_INT_S)))
  time.sleep(WINDOW_INT_S)
  # os.system('clear')


""" for frame_number in range(FRAME_COUNT):
  sample = extract_sample(audio, frame_number)

  fft = np.fft.rfft(sample * window)
  fft = np.abs(fft) / mx
  

  fig = plot_fft(fft.real,xf,fs,RESOLUTION,max(fft))
  fig.write_image(f"/Users/aryan/dev/misc/spotify-rgb-sync/analysis/frames/frame{frame_number}.png", scale=2) """
