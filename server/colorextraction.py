import math
from PIL import Image, ImageDraw
from collections import namedtuple
import cv2
from mmcq_numba.quantize import mmcq
from pprint import pprint
import numpy as np


class Swatch:
    hsl = None
    rgb = None
    population = 1
    yiq = 0

    def __init__(self, rgb, population):
        self.rgb = rgb
        self.population = population

    def get_hsl(self):
        if not self.hsl:
            self.hsl = self.rgb_to_hsl(self.rgb[0], self.rgb[1], self.rgb[2])
        
        return self.hsl
    
    def rgb_to_hsl(self, r, g, b):
        r /= 255.0
        g /= 255.0
        b /= 255.0

        max_val = max(r, g, b)
        min_val = min(r, g, b)
        h = 0
        s = 0
        # Calculate lightness (L)
        l = (max_val + min_val) / 2.0

        if max_val == min_val:
            # Achromatic (gray)
            h = 0
            s = 0
        else:
            d = max_val - min_val

            # Calculate saturation (S)
            if l > 0.5:
                s = d / (2.0 - max_val - min_val)
            else:
                s = d / (max_val + min_val)

            # Calculate hue (H)
            if max_val == r:
                h = (g - b) / d + (6.0 if g < b else 0.0)
            elif max_val == g:
                h = (b - r) / d + 2.0
            else:
                h = (r - g) / d + 4.0

            h /= 6.0

        return h, s, l

    def get_population(self):
        return self.population

    def get_rgb(self):
        return self.rgb

    def get_hex(self):
        return "#{:02x}{:02x}{:02x}".format(self.rgb[0], self.rgb[1], self.rgb[2])
    

    def get_title_text_color(self):
        self._ensure_text_colors()
        return "#fff" if self.yiq < 200 else "#000"

    def get_body_text_color(self):
        self._ensure_text_colors()
        return "#fff" if self.yiq < 150 else "#000"

    def _ensure_text_colors(self):
        if not self.yiq:
            self.yiq = (self.rgb[0] * 299 + self.rgb[1] * 587 + self.rgb[2] * 114) / 1000

class Vibrant:
    _swatches = []

    TARGET_DARK_LUMA = 0.26
    MAX_DARK_LUMA = 0.45
    MIN_LIGHT_LUMA = 0.55
    TARGET_LIGHT_LUMA = 0.74

    MIN_NORMAL_LUMA = 0.3
    TARGET_NORMAL_LUMA = 0.5
    MAX_NORMAL_LUMA = 0.7

    TARGET_MUTED_SATURATION = 0.3
    MAX_MUTED_SATURATION = 0.4

    TARGET_VIBRANT_SATURATION = 1
    MIN_VIBRANT_SATURATION = 0.35

    WEIGHT_SATURATION = 3
    WEIGHT_LUMA = 6
    WEIGHT_POPULATION = 1

    VibrantSwatch = None
    MutedSwatch = None
    DarkVibrantSwatch = None
    DarkMutedSwatch = None
    LightVibrantSwatch = None
    LightMutedSwatch = None

    VibrantPallete = []

    HighestPopulation = 0

    def __init__(self, source_image, color_count= 64, quality= 5):
        if not color_count:
            color_count = 64
        if not quality:
            quality = 5
        self._swatches = []
        self.VibrantSwatch = None
        self.MutedSwatch = None
        self.DarkVibrantSwatch = None
        self.DarkMutedSwatch = None
        self.LightVibrantSwatch = None
        self.LightMutedSwatch = None
        self.HighestPopulation = 0
        im = Image.open(source_image)
        
        image = CanvasImage(im)
        try:
            pixelCount = image.getPixelCount()
            pixels = image.pixeldata
            all_pixels = []
            i = 0
            while i < pixelCount:
                
                
                y = i // image.width
                x = i - y * image.width
                r = pixels[x, y][0]
                g = pixels[x, y][1]
                b = pixels[x, y][2]
                a = pixels[x, y][3]
                #if pixel is mostly opaque and not white
                if a >= 125 and not (r > 250 and g > 250 and b > 250):
                    all_pixels.append([r, g, b])
                i += quality
            colorpixels = np.array(all_pixels)
            colorpixels= colorpixels.astype(np.int64)
            cmap = mmcq(colorpixels, color_count)
            self._swatches = [Swatch(list(cmap.vbox.values())[1], pixelCount) for cmap.vbox in cmap.vboxes]
            self.max_population = self.find_max_population()
            self.generate_variation_colors()
            self.generate_empty_swatches()
        finally:
            image.clear()
    def generate_variation_colors(self):
        self.VibrantSwatch = self.find_color_variation(
            self.TARGET_NORMAL_LUMA, self.MIN_NORMAL_LUMA, self.MAX_NORMAL_LUMA,
            self.TARGET_VIBRANT_SATURATION, self.MIN_VIBRANT_SATURATION, 1)
        self.LightVibrantSwatch = self.find_color_variation(
            self.TARGET_LIGHT_LUMA, self.MIN_LIGHT_LUMA, 1,
            self.TARGET_VIBRANT_SATURATION, self.MIN_VIBRANT_SATURATION, 1)
        self.DarkVibrantSwatch = self.find_color_variation(
            self.TARGET_DARK_LUMA, 0, self.MAX_DARK_LUMA,
            self.TARGET_VIBRANT_SATURATION, self.MIN_VIBRANT_SATURATION, 1)
        self.MutedSwatch = self.find_color_variation(
            self.TARGET_NORMAL_LUMA, self.MIN_NORMAL_LUMA, self.MAX_NORMAL_LUMA,
            self.TARGET_MUTED_SATURATION, 0, self.MAX_MUTED_SATURATION)
        self.LightMutedSwatch = self.find_color_variation(
            self.TARGET_LIGHT_LUMA, self.MIN_LIGHT_LUMA, 1,
            self.TARGET_MUTED_SATURATION, 0, self.MAX_MUTED_SATURATION)
        self.DarkMutedSwatch = self.find_color_variation(
            self.TARGET_DARK_LUMA, 0, self.MAX_DARK_LUMA,
            self.TARGET_MUTED_SATURATION, 0, self.MAX_MUTED_SATURATION)
        
    def generate_vibrant_pallete(self):
        for _ in range(3):
            self.VibrantPallete.append(self.find_color_variation(
                self.TARGET_NORMAL_LUMA, self.MIN_NORMAL_LUMA, self.MAX_NORMAL_LUMA,
                self.TARGET_VIBRANT_SATURATION, self.MIN_VIBRANT_SATURATION, 1
            ))
        for _ in range(3):
            self.VibrantPallete.append(self.find_color_variation(
                self.TARGET_NORMAL_LUMA, self.MIN_NORMAL_LUMA, 1,
                self.TARGET_VIBRANT_SATURATION, self.MIN_VIBRANT_SATURATION, 1
            ))

    def generate_empty_swatches(self):
        if self.VibrantSwatch is None:
            if self.DarkVibrantSwatch is not None:
                hsl = self.DarkVibrantSwatch.get_hsl()
                hsl[2] = self.TARGET_NORMAL_LUMA
                self.VibrantSwatch = Swatch(self.hsl_to_rgb(hsl[0], hsl[1], hsl[2]), 0)

        if self.DarkVibrantSwatch is None:
            if self.VibrantSwatch is not None:
                hsl = self.VibrantSwatch.get_hsl()
                hsl[2] = self.TARGET_DARK_LUMA
                self.DarkVibrantSwatch = Swatch(self.hsl_to_rgb(hsl[0], hsl[1], hsl[2]), 0)


    
    


    def find_max_population(self):
        population = 0
        for swatch in self._swatches:
            population = max(population, swatch.get_population())
        return population
    
    def  is_already_selected(self, swatch):
        return (
            swatch == self.VibrantSwatch or
            swatch == self.DarkVibrantSwatch or
            swatch == self.LightVibrantSwatch or
            swatch == self.MutedSwatch or
            swatch == self.DarkMutedSwatch or
            swatch == self.LightMutedSwatch or
            swatch in self.VibrantPallete
        )
    def find_color_variation(self, target_luma, min_luma, max_luma, target_saturation, min_saturation, max_saturation):
        max_value = 0
        max_swatch = None

        for swatch in self._swatches:
            sat = swatch.get_hsl()[1]
            luma = swatch.get_hsl()[2]

            if (min_saturation <= sat <= max_saturation and
                min_luma <= luma <= max_luma and
                not self.is_already_selected(swatch)):
                value = self.create_comparison_value(
                    sat, target_saturation, luma, target_luma,
                    swatch.get_population(), 1 if(self.HighestPopulation == 0) else self.HighestPopulation
                )
                if max_swatch is None or value > max_value:
                    max_swatch = swatch
                    max_value = value

        return max_swatch

    def create_comparison_value(self, saturation, target_saturation, luma, target_luma, population, max_population):
        return self.weighted_mean(
            self.invert_diff(saturation, target_saturation), self.WEIGHT_SATURATION,
            self.invert_diff(luma, target_luma), self.WEIGHT_LUMA,
            population / max_population, self.WEIGHT_POPULATION
        )

    @staticmethod
    def invert_diff(value, target_value):
        return 1 - abs(value - target_value)

    @staticmethod
    def weighted_mean(*values):
        sum_values = 0
        sum_weight = 0
        i = 0
        while i < len(values):
            value = values[i]
            weight = values[i + 1]
            sum_values += value * weight
            sum_weight += weight
            i += 2
        return sum_values / sum_weight

    def swatches(self):
        return {
            "Vibrant": self.VibrantSwatch,
            "Muted": self.MutedSwatch,
            "DarkVibrant": self.DarkVibrantSwatch,
            "DarkMuted": self.DarkMutedSwatch,
            "LightVibrant": self.LightVibrantSwatch,
            "LightMuted": self.LightMutedSwatch
        }

    @staticmethod
    def rgb_to_hsl(r, g, b):
        r /= 255
        g /= 255
        b /= 255
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        h = s = l = (max_val + min_val) / 2

        if max_val == min_val:
            h = s = 0
        else:
            d = max_val - min_val
            s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
            if max_val == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_val == g:
                h = (b - r) / d + 2
            elif max_val == b:
                h = (r - g) / d + 4
            h /= 6

        return [h, s, l]

    @staticmethod
    def hsl_to_rgb(h, s, l):
        def hue2rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        r, g, b = 0, 0, 0

        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue2rgb(p, q, h + 1 / 3)
            g = hue2rgb(p, q, h)
            b = hue2rgb(p, q, h - 1 / 3)

        return [r * 255, g * 255, b * 255]




class CanvasImage:
    def __init__(self, image):
        self.canvas = image.convert("RGBA")
        self.pixeldata = self.canvas.load()
        self.context = ImageDraw.Draw(self.canvas)
        self.width = image.width
        self.height = image.height

    def clear(self):
        self.context.rectangle([0, 0, self.width, self.height], fill=(0, 0, 0, 0))

    def update(self, imageData):
        self.canvas.paste(imageData, (0, 0))

    def getPixelCount(self):
        return self.width * self.height
    

    def removeCanvas(self):
        # In Python, there's no direct equivalent to removing a canvas element from the DOM.
        # You can just discard the instance of the CanvasImage class if you no longer need it.
        pass