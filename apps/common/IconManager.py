import pygame
import os

base_path = os.path.dirname(__file__)

def load_image_relative(path):
    image_path = os.path.join(base_path, path)
    return pygame.image.load(image_path)

radioconsole_icons = {
    'warning': load_image_relative("warning.png"),
    'raspberrypi': load_image_relative("raspberry_pi.png"),
    'satellite': load_image_relative("satellite.png"),
    'signal': load_image_relative("signal.png"),
    'services': load_image_relative("services.png"),
    'gps_satellite': load_image_relative("gps_satellite.png"),
    'power': load_image_relative("power.png"),
    'direwuff': load_image_relative("direwuff.png")
}

def colour_image(image, colour, colourname):
    radioconsole_icons[f'{image}_{colourname}'] = radioconsole_icons[image].copy()
    radioconsole_icons[f'{image}_{colourname}'].fill(colour, None, pygame.BLEND_MULT)

colour_image('warning', (255,0,0,255), 'red')
colour_image('warning', (255,165,0,255), 'orange')

colour_image('gps_satellite', (255,0,0,255), 'red')
colour_image('gps_satellite', (0,255,0,255), 'green')
colour_image('gps_satellite', (0,0,255,255), 'blue')
colour_image('gps_satellite', (255,165,0,255), 'orange')
colour_image('gps_satellite', (0,255,255,255), 'cyan')
colour_image('gps_satellite', (255,0,255,255), 'magenta')
colour_image('gps_satellite', (255,255,0,255), 'yellow')

def darken_image(image):
    colour_image(image, (64,64,64,255), "dark")

darken_image('raspberrypi')
darken_image('satellite')
darken_image('signal')
darken_image('services')
darken_image('power')
darken_image('direwuff')