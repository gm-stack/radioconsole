import pygame

radioconsole_icons = {
    'warning': pygame.image.load("apps/common/warning.png"),
    'raspberrypi': pygame.image.load("apps/common/raspberry_pi.png"),
    'satellite': pygame.image.load("apps/common/satellite.png"),
    'signal': pygame.image.load("apps/common/signal.png"),
    'services': pygame.image.load("apps/common/services.png"),
    'gps_satellite': pygame.image.load("apps/common/gps_satellite.png"),
    'power': pygame.image.load("apps/common/power.png"),
    'direwuff': pygame.image.load("apps/common/direwuff.png")
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