from colorist import ColorRGB
import os
import pygame as pg


def display_tree(layout, gen):
    pg.init()
    window_w, window_h = 512, 512
    bg = (30,30,50)

    window = pg.display.set_mode((window_w, window_h))
    pg.display.set_caption("Twinkly Visualiser")
    window.fill(bg)

    min_x, max_x = min(c['x'] for c in layout), max(c['x'] for c in layout)
    min_y, max_y = min(c['y'] for c in layout), max(c['y'] for c in layout)

    dx = max_x - min_x or 1
    dy = max_y - min_y or 1

    for c in layout:
        c['x'] = ((c['x'] - min_x) / dx)
        c['y'] = ((c['y'] - min_y) / dy)

    # visual parameters
    led_radius = 6
    pad = led_radius * 3  # padding so LEDs near edges do not get clipped

    # create a drawing surface that includes padding around the normalized coordinates
    surf_w = window_w + pad * 2
    surf_h = window_h + pad * 2
    surface = pg.Surface((surf_w, surf_h))

    # initial view transform
    zoom = 1.0

    rect = surface.get_rect(center=window.get_rect().center)

    clock = pg.time.Clock()

    running = True
    while running:
        sw = (surf_w - pad * 2)
        sh = (surf_h - pad * 2)
        for frame in gen:
            surface.fill(bg)

            # draw LEDs with padding offset so the full circle can be visible at edges
            for x in range(len(layout)):
                c = layout[x]
                _, r, g, b = frame[x]

                cx = int(pad + c['x'] * sw)
                cy = int(pad + (1 - c['y']) * sh)

                # draw background halo for better visibility when colors are dark
                if (r, g, b) == (0, 0, 0):
                    color = (20, 20, 20)
                else:
                    color = (r, g, b)

                pg.draw.circle(surface, color, (cx, cy), led_radius)

            # scale the surface according to current zoom and blit using the rect for panning
            scaled_size = (max(1, int(surf_w * zoom)), max(1, int(surf_h * zoom)))
            scaled_win = pg.transform.scale(surface, scaled_size)

            # preserve the current center when zooming
            prev_center = rect.center
            rect = scaled_win.get_rect()
            rect.center = prev_center

            window.fill(bg)
            window.blit(scaled_win, rect)
            pg.display.flip()

            for e in pg.event.get():
                if e.type == pg.QUIT or (e.type == pg.KEYUP and e.key == pg.K_ESCAPE):
                    print("Exiting...")
                    running = False
                elif e.type == pg.KEYUP:
                    # zoom in/out with + and -
                    if e.key == pg.K_EQUALS or e.key == pg.K_PLUS:
                        zoom *= 1.1
                    elif e.key == pg.K_MINUS or e.key == pg.K_UNDERSCORE:
                        zoom *= 0.9

                    # panning with arrow keys
                    elif e.key == pg.K_LEFT:
                        rect.x += 20
                    elif e.key == pg.K_RIGHT:
                        rect.x -= 20
                    elif e.key == pg.K_UP:
                        rect.y += 20
                    elif e.key == pg.K_DOWN:
                        rect.y -= 20

            clock.tick(100)

            if not running:
                break


def print_tree(frame):
    os.system('clear')
    for y in range(25):
        row = ""
        for x in range(10):
            _, r, g, b = frame[x]
            if (r, g, b) == (0, 0, 0):
                row += ". "
                continue
            else:
                color = ColorRGB(r, g, b)
                row += f"{color}# {color.OFF}"
        print(row)
    print("\n")