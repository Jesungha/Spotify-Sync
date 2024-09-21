from analysis import generate_normalized_array
from pprint import pprint

def gen_show(pallette, audio_frames):
    # 30 minute spoof sequence
    seq = []

    for p in audio_frames:
        total = sum(p)
        if total == 0:
            seq.append((0, 0, 0))
            continue
        r,g,b = 0,0,0
        for i in range(len(p)):
            rate = p[i]/total
            r += pallette[i][0] * rate
            g += pallette[i][1] * rate
            b += pallette[i][2] * rate
        
        
        seq.append((int(r), int(g), int(b)))

    return seq

if __name__ == "__main__":
    show =gen_show(
        [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (139, 0, 255)],
        generate_normalized_array("./out/6LyAwkJsHlW7RQ8S1cYAtM.wav", 50)
    )
    pprint(show)