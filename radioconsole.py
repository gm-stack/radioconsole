import sys

import pygame

import config
import top_bar
import WaterfallDisplay
import FFTData


if __name__ == '__main__':
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((config.DISPLAY_W, config.DISPLAY_H))

    tb = top_bar.TopBar((0, 0, config.DISPLAY_W, config.TOP_BAR))

    fftd = FFTData.FFTData(
        provider=config.SAMPLE_PROVIDER,
        cfg=''
    )
    wd = WaterfallDisplay.WaterfallDisplay(
        fftd, 
        (0, config.TOP_BAR, config.DISPLAY_W, config.DISPLAY_H - config.TOP_BAR)
    )

    while True:
        for e in pygame.event.get():
            if e.type is pygame.KEYDOWN:
                k = pygame.key.name(e.key)
                m = pygame.key.get_mods()
                tb.keydown(k,m) or wd.keydown(k,m)
            elif e.type is pygame.QUIT:
                pygame.quit()
                sys.exit()

        tb.draw(screen)
        wd.draw(screen)
        pygame.display.update()