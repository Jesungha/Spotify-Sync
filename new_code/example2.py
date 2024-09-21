import colorextraction as ce
from PIL import Image, ImageDraw
img =  'temp_image3.jpg'

img = ce.Vibrant(img)
img.generate_vibrant_pallete()
for i, c in enumerate(img.VibrantPallete):
    im = Image.new("RGB", (100, 100), c.get_hex())
    im.save("output" + str(i) +".png")