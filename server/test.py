import colorextraction as ce
from PIL import Image, ImageDraw
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
        print(rgbcolors)
    return rgbcolors

retrieve_song_art("temp_image")