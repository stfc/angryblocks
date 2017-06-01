#!/usr/bin/env python2

import pygame, time, math, ConfigParser
from random import randint
from pygame.locals import *
from collections import namedtuple


def isPointInsideRect(x, y, rect):
    if (x > rect.left) and (x < rect.right) and (y > rect.top) and (y < rect.bottom):
        return True

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

POWER_STEP = 2
ANGLE_STEP = 2


class AngryBlocksGame(object):

    def __init__(self, config):
        self.score = 0
        self.projectile = None
        self.vx = 0
        self.vy = 0
        self.fired = False
        self.target = None
        self.misses = 0
        self.canvas = None
        self.textBuffer = None
        self.text_draw_time = 0
        self.multiplier = 1

        # Initialise pygame
        pygame.init()

        # Set window caption
        pygame.display.set_caption("Angry Blocks")

        # Initialise the clock
        self.mainClock = pygame.time.Clock()

        # Set window size
        self.windowheight = 768
        self.windowwidth = 1024

        # Initialise our window
        self.windowSurface = pygame.display.set_mode((self.windowwidth, self.windowheight), HWSURFACE, 32)
        self.canvas = pygame.Surface((self.windowwidth, self.windowheight))
        self.windowBuffer = pygame.Surface((self.windowwidth, self.windowheight))
        self.textBuffer = pygame.Surface((self.windowwidth, self.windowheight))

        self.canvas.set_alpha(63)
        # Set the background colour
        self.canvas.fill(BLACK)

        # Load sound effects
        sound_list = ['fire', 'miss', 'hit', 'bounce', 'lose']
        self.sounds = namedtuple('Sound', sound_list)
        for sound in sound_list:
            setattr(self.sounds, sound, pygame.mixer.Sound(config.get('sound', sound)))

        #Create power meter
        self.powermeter = pygame.Rect(0, 0, 0, 4)

        # Create projectile box and home square
        self.projectile = pygame.Rect(0, 0, 60, 60)
        self.origin = pygame.Rect(0, self.windowheight - 65, 60, 60)

        self.TARGETX = 0
        self.TARGETY = 0

        self.MISS_LIMIT = 3

        # Create target
        self.target = pygame.Rect(self.TARGETX, self.TARGETY, 30, 30)

        self.genfont = pygame.font.SysFont("Arial", 72)
        self.scorefont = pygame.font.SysFont("Arial", 24)
        self.textHit = self.genfont.render("HIT", True, WHITE)
        self.textMiss = self.genfont.render("MISS", True, WHITE)

        self.vx, self.vy = 0, 0
        self.fired = False
        self.score = 0
        self.misses = 0

        self.text_draw_time = 0

        self.realTime = 0
        self.powering = False

        self.power = 10
        self.angle = 40.0
        self.radangle = self.angle*math.pi/180.0

        # Set Acceleration
        self.ax = 0
        self.ay = 2 # Make this bigger for more gravity

        self.home_x = 30
        self.home_y = self.windowheight - 32

        self.reset()
        self.reset_target()

        pygame.mixer.music.load(config.get('sound', 'music'))
        pygame.mixer.music.play(-1)

        self.drawtext("Angry Blocks")

    def drawtext(self, txt):
        x = self.windowwidth / 2
        y = self.windowheight / 2

        if isinstance(txt, str):
            txt = self.genfont.render(txt, True, WHITE)

        r = txt.get_rect()
        r.centerx = x
        r.centery = y
        self.textBuffer.fill(BLACK)
        self.textBuffer.blit(txt, r)
        self.text_draw_time = int(time.time())

    def drawscore(self):
        txt = self.scorefont.render("Score: %d  Multiplier: %d" % (self.score, self.multiplier), True, WHITE)
        r = txt.get_rect()
        r.topleft = 0, 0
        self.canvas.blit(txt, r)

    def drawdebug(self, text):
        txt = self.scorefont.render(text, True, WHITE)
        r = txt.get_rect()
        r.topright = self.windowwidth, 0
        self.canvas.blit(txt, r)

    def reset(self):
        self.projectile.x = 0
        self.projectile.y = self.windowheight - 65
        self.vx, self.vy = 0, 0
        self.fired = False

    def reset_target(self):
        self.target.x = self.windowwidth / 2 + randint(0, self.windowwidth / 2) - 30
        self.target.y = randint(0, self.windowheight - 30)
        self.misses = 0

    def miss(self):
        self.sounds.miss.play()
        self.misses += 1
        self.multiplier = 1
        self.drawtext("Miss " + str(self.misses) + " of " + str(self.MISS_LIMIT))
        if self.misses >= self.MISS_LIMIT:
            self.sounds.lose.play()
            self.reset_target()
            self.misses = 0
            self.score -= 1
        self.reset()

    def run(self):
        running = True

        # This is the main game loop
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    running = False
                    break

                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()

                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1 and not self.fired:
                        self.powering = True

                elif event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        if not self.fired and self.powering:
                            self.sounds.fire.play()
                            self.powering = False
                            self.fired = True
                            # calculate the initial velocitys for the projectile
                            self.vx = (self.power / 1.5) * math.sin(self.radangle)
                            self.vy = -(self.power / 1.5) * math.cos(self.radangle)
                            self.power = 10
            if running:
                if self.fired:
                    # Calculate our co-ordinates

                    # Bounce
                    if (self.projectile.bottom + self.vy) >= self.windowheight:
                        self.sounds.bounce.play()
                        self.vy = -self.vy * 0.75
                        self.vx = self.vx * 0.75
                        self.multiplier += 1

                    # Update the velocities from the accelerations
                    self.vx += self.ax
                    self.vy += self.ay

                    # Move the box down and left
                    # use the velocities to update the position
                    self.projectile.left += self.vx
                    self.projectile.top += self.vy

                elif self.powering:
                    self.power = min(110, max(10, self.power + POWER_STEP))

                # Clear the screen
                self.windowSurface.fill(BLACK, None)
                self.canvas.fill(BLACK, None)

                # Draw our projectile
                pygame.draw.rect(self.canvas, RED, self.projectile)

                # Blur the canvas
                self.blur = pygame.transform.smoothscale(self.canvas, (int(self.windowwidth/8), int(self.windowheight/8)))
                self.canvas = pygame.transform.smoothscale(self.blur, (self.windowwidth, self.windowheight))

                # Draw the projectile again for crispness
                pygame.draw.rect(self.canvas, RED, self.projectile)

                # Draw the target
                pygame.draw.rect(self.canvas, GREEN, self.target)

                (ma_x, ma_y) = pygame.mouse.get_pos()
                mr_x = ma_x - self.home_x
                mr_y = ma_y - self.home_y
                self.radangle = math.atan2(mr_x, -mr_y)

                #self.drawdebug('%d, %d = %f' % (mr_x, mr_y, math.degrees(self.radangle)))

                self.drawdebug('%d FPS' % self.mainClock.get_fps())

                # Draw power meter
                fpower = self.power / 110.0
                ipower = int(255 * fpower)
                cpower = (ipower, ipower / 2, 255 - ipower)

                self.powermeter.width = int(self.windowwidth / 100.0 * (self.power - 10))
                pygame.draw.rect(self.canvas, cpower, self.powermeter)

                # Draw arrow (scaled with power)
                pm_x = self.home_x + (math.sin(self.radangle) * 2 * self.power)
                pm_y = self.home_y - (math.cos(self.radangle) * 2 * self.power)

                ah_x = self.home_x + (math.sin(self.radangle + 5*math.pi/180.0) * 1.8 * self.power)
                ah_y = self.home_y - (math.cos(self.radangle + 5*math.pi/180.0) * 1.8 * self.power)

                bh_x = self.home_x + (math.sin(self.radangle + -5*math.pi/180.0) * 1.8 * self.power)
                bh_y = self.home_y - (math.cos(self.radangle + -5*math.pi/180.0) * 1.8 * self.power)

                pygame.draw.aaline(self.canvas, WHITE, (pm_x, pm_y), (ah_x, ah_y))
                pygame.draw.aaline(self.canvas, WHITE, (pm_x, pm_y), (bh_x, bh_y))
                pygame.draw.aaline(self.canvas, WHITE, (self.home_x, self.home_y), (pm_x, pm_y))
                pygame.draw.rect(self.canvas, WHITE, self.origin, 1)

                # Draw score
                self.drawscore()

                # Update the screen
                self.windowBuffer.blit(self.canvas, (0, 0))
                self.windowSurface.blit(self.windowBuffer, (0, 0))

                # Only blit text buffer if it has been recently updated
                render_time = int(time.time())
                if render_time - self.text_draw_time < 3:
                    if render_time - self.text_draw_time > 1:
                        self.textBuffer = pygame.transform.smoothscale(
                            self.textBuffer,
                            (int(self.windowwidth / 8), int(self.windowheight / 8))
                        )
                        self.textBuffer = pygame.transform.smoothscale(
                            self.textBuffer,
                            (self.windowwidth, self.windowheight)
                        )
                    self.windowSurface.blit(self.textBuffer, (0, 0), special_flags=BLEND_ADD)

                pygame.display.update()

                # If the box leaves the screen, miss
                if not self.windowSurface.get_rect().contains(self.projectile):
                    self.miss()

                # If the box stops, miss
                if self.fired and abs(self.vy) <= 0:
                    self.miss()

                # If the projectile hits the target
                if self.projectile.colliderect(self.target):
                    self.sounds.hit.play()
                    self.score += (1 * self.multiplier)
                    self.drawtext(self.textHit)
                    self.reset()
                    self.reset_target()

                # Wait for a short time
                self.mainClock.tick(60)


def main():
    config = ConfigParser.ConfigParser()
    config.readfp(open('defaults.cfg'))
    config.read(['game.cfg'])

    game = AngryBlocksGame(config)
    game.run()

if __name__ == "__main__":
    main()
