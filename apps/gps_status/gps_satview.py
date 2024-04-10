import math

import pygame
import pygame.gfxdraw
import pygame.math
from pygame import surface
from ..common.IconManager import radioconsole_icons

GNSS_IDS={
    0: {
        "prefix": "GP",
        "name": "GPS",
        "colour": 'white'
    },
    1: {
        "prefix": "SB",
        "name": "GPS SBAS",
        "colour": "yellow"
    },
    2: {
        "prefix": "GA",
        "name": "Galileo",
        "colour": "cyan"
    },
    3: {
        "prefix": "BD",
        "name": "BeiDou",
        "colour": "red"
    },
    4: {
        "prefix": "IM",
        "name": "IMES",
        "colour": "green"
    },
    5: {
        "prefix": "QZ",
        "name": "QZSS",
        "colour": "green"
    },
    6: {
        "prefix": "GL",
        "name": "GLONASS",
        "colour": "orange"
    }
}

class gps_satview(object):
    surf = None
    sky = None
    text_colour = (0xCC,0xCC,0xCC)

    def __init__(self, bounds):
        self.font = pygame.font.Font("ttf/B612-Regular.ttf", 16)
        self.bigfont = pygame.font.Font("ttf/B612-Regular.ttf", 24)
        self.bounds = bounds
        self.surf = surface.Surface(self.bounds.size)
        self.sat_icons = {
            icon_name.split("_")[-1]: icon
            for icon_name, icon in radioconsole_icons.items()
            if icon_name.startswith('gps_satellite')
        }
        self.sat_icons['white'] = radioconsole_icons['gps_satellite']
        print(self.sat_icons)
        self.sat_icon_halfsize = pygame.math.Vector2(
            self.sat_icons['white'].get_width() / 2, 
            self.sat_icons['white'].get_height() / 2
        )

    def gps_mode(self, m):
        return {
            0: 'UNK',
            1: 'NONE',
            2: '2D',
            3: '3D'
        }.get(m,'?')
    
    def gps_colour(self, m):
        return {
            '3D': (0, 255, 0, 255),
            '2D': (255, 255, 0, 255)
        }.get(m, (255, 0, 0, 255))

    def update_data(self, data, tpv, mh):
        self.sky = data

        self.surf.fill((0, 0, 0))
        self.surf.lock()

        satview_radius = 150
        satview_centre = pygame.math.Vector2(200,210)
        
        for i in range(1, satview_radius, int(satview_radius / 10)):
            pygame.gfxdraw.aacircle(self.surf, int(satview_centre[0]), int(satview_centre[1]), i, (0, 255, 0))
        for i in range(0, 359, 10):
            end = pygame.math.Vector2(math.cos(math.radians(i)), math.sin(math.radians(i)))
            pygame.draw.aaline(
                self.surf, 
                (0, 255, 0), 
                satview_centre, 
                satview_centre + (end * satview_radius)
            )
        self.surf.unlock()

        for sat in self.sky:
            sat_az = math.radians(sat['az'])
            sat_direction = pygame.math.Vector2(math.cos(sat_az), math.sin(sat_az))
            sat_el = 90 - sat['el'] # elevation 90 is in centre, elevation 0 is at edge
            sat_offset = sat_direction * sat_el * (satview_radius / 90.0)
            sat_pos = satview_centre + sat_offset - self.sat_icon_halfsize

            sat_info = GNSS_IDS.get(sat['gnssid'], {})
            sat_colour = sat_info.get('colour', 'magenta')

            self.surf.blit(self.sat_icons[sat_colour], sat_pos)

        lat = tpv.get('lat')
        lon = tpv.get('lon')
        if lat and lon:
            lat_text = self.font.render(f"{lat:.6f}°", True, self.text_colour)
            lon_text = self.font.render(f"{lon:.6f}°", True, self.text_colour)
            self.surf.blit(lat_text, (4,4))
            self.surf.blit(lon_text, (124,4))
        alt = tpv.get('alt')
        if alt:
            alt_text = self.font.render(f"{alt:.1f}m", True, self.text_colour)
            self.surf.blit(alt_text, (244,4))

        gps_mode = self.gps_mode(tpv.get('mode'))
        mode_text = self.bigfont.render(gps_mode, True, self.gps_colour(gps_mode))
        self.surf.blit(mode_text, (self.bounds.w-(mode_text.get_width()), 4))


        numsats = len(self.sky)
        numused = len([i for i in self.sky if i['used']])
        sats_text = self.bigfont.render(f"{numused}/{numsats}", True, self.gps_colour(gps_mode))
        self.surf.blit(sats_text, (self.bounds.w-(sats_text.get_width()), 4 + mode_text.get_height()))
        
        mh_text = self.bigfont.render(mh, True, self.text_colour)
        self.surf.blit(mh_text, (self.bounds.w-(mh_text.get_width()), (self.bounds.h - mh_text.get_height() - 4)))

        v = tpv.get('speed', 0)
        spd_text = self.bigfont.render(f"{float(v)*3.6:.1f}km/h", True, self.text_colour)
        self.surf.blit(spd_text, (4, (self.bounds.h - mh_text.get_height() - 4)))



    def draw(self, screen):
        screen.blit(self.surf, self.bounds.topleft)
