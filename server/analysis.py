import matplotlib.pyplot as plt
from scipy.fftpack import fft
from scipy.io import wavfile # get the api
import numpy as np
import time
import threading
import playsound

FPS = 30 # frames per second
FFT_WINDOW_SECONDS = 0.25 # seconds

def extract_sample(audio, frame_number, offset, window_size):
  end = frame_number * offset
  begin = int(end - window_size)

  if end == 0:
    # We have no audio yet, return all zeros (very beginning)
    return np.zeros((np.abs(begin)),dtype=float)
  elif begin<0:
    # We have some audio, padd with zeros
    return np.concatenate([np.zeros((np.abs(begin)),dtype=float),audio[0:end]])
  else:
    # Usually this happens, return the next sample
    return audio[begin:end]

def generate_normalized_array(wav_file, interval):
    fs, data = wavfile.read(wav_file) # load the data
    audio = data.T[0] # this is a two channel soundtrack, get the first track
    FRAME_STEP = (fs / FPS) # audio samples per video frame
    FFT_WINDOW_SIZE = int(fs * FFT_WINDOW_SECONDS) # seconds
    AUDIO_LENGTH = len(audio)/fs # seconds

    window = 0.5 * (1 - np.cos(np.linspace(0, 2*np.pi, FFT_WINDOW_SIZE, False)))

    FRAME_COUNT = int(AUDIO_LENGTH*FPS) # frames
    FRAME_OFFSET = int(len(audio)/FRAME_COUNT) # samples

    WINDOW_INT_S = interval/1000
    WINDOW_CNT = int(AUDIO_LENGTH/(WINDOW_INT_S))
    
    xf = np.fft.rfftfreq(FFT_WINDOW_SIZE, 1/fs)

    mx = 0
    for frame_number in range(FRAME_COUNT):
        sample = extract_sample(audio, frame_number, FRAME_OFFSET, FFT_WINDOW_SIZE)

        fft = np.fft.rfft(sample * window)
        fft = np.abs(fft).real 
        mx = max(np.max(fft),mx)

    mins = [1] * 7
    maxs = [0] * 7
    for i in range(WINDOW_CNT):
        frame = int(FPS*(i*WINDOW_INT_S))
        sample = extract_sample(audio, frame, FRAME_OFFSET, FFT_WINDOW_SIZE)

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

    normalized_array = []
    for i in range(WINDOW_CNT):
        frame = int(FPS*(i*WINDOW_INT_S))
        sample = extract_sample(audio, frame, FRAME_OFFSET, FFT_WINDOW_SIZE)

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
        
        normalized_array.append(y_new)

    return normalized_array

if __name__ == "__main__":
    sample_path = "./out/2i2gDpKKWjvnRTOZRhaPh2.wav"
    start_time = time.time()
    interval = 50
    arr = generate_normalized_array(sample_path, interval)
    end_time = time.time()
    print(f"Time taken to generate normalized array: {end_time - start_time} seconds")
    print(len(arr))
    
    threading.Thread(target=playsound, args=(sample_path,), daemon=True).start()

    for a in arr:
        s = ""
        for i, d in enumerate(a):
            level = int(d*10)
            s += str(i)+": "+"=" * level + " " * (10-level) + "\n"
        print("\033c", end="")
        print(s)
        # clear console
        time.sleep(interval/1000)
    print("Done")