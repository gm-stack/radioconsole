import pygame

radioconsole_icons = {
    'warning': pygame.image.load("apps/common/warning.png"),
    'raspberrypi': pygame.image.load("apps/common/raspberry_pi.png"),
    'satellite': pygame.image.load("apps/common/satellite.png"),
    'signal': pygame.image.load("apps/common/signal.png"),
    'services': pygame.image.load("apps/common/services.png"),
}
            
radioconsole_icons['redalert'] = radioconsole_icons['warning'].copy()
radioconsole_icons['redalert'].fill((255,0,0,255), None, pygame.BLEND_MULT)

radioconsole_icons['orangealert'] = radioconsole_icons['warning'].copy()
radioconsole_icons['orangealert'].fill((255,165,0,255), None, pygame.BLEND_MULT)

def darken_image(image):
    radioconsole_icons[f'{image}_dark'] = radioconsole_icons[image].copy()
    radioconsole_icons[f'{image}_dark'].fill((64,64,64,255), None, pygame.BLEND_MULT)

darken_image('raspberrypi')
darken_image('satellite')
darken_image('signal')
darken_image('services')