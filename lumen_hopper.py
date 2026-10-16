#!/usr/bin/env python3
"""Lumen Hopper — neon tide-hopper arcade for ElbowOS. Python 3 + pygame.
Hop a glowing orb across vertical neon lanes of speeding craft.
Reach the top for bonus, avoid collisions.
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/LUMEN_HOPPER_ElbowOS.mp4")
TITLE, HANDLE = "LUMEN HOPPER", "x.com/ElbowOS"

# Neon palette
BG = (8, 6, 22)
LANE_BG = (18, 14, 40)
CYAN = (0, 255, 255)
MAG = (255, 0, 180)
LIME = (120, 255, 80)
GOLD = (255, 220, 60)
ROSE = (255, 80, 140)
WHITE = (240, 245, 255)
PLAYER_COL = (80, 255, 180)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("dejavusans", 72, bold=True)
        self.font = pygame.font.SysFont("dejavusans", 48, bold=True)
        self.font_sm = pygame.font.SysFont("dejavusans", 32)
        self.reset()

    def reset(self):
        self.score = 0
        self.px = W // 2
        self.py = H - 180
        self.pvx = 0
        self.pvy = 0
        self.alive = True
        self.reached = 0
        self.lanes = []
        lane_h = 140
        n_lanes = 10
        for i in range(n_lanes):
            y = H - 280 - i * lane_h
            if y < 200:
                break
            direction = 1 if i % 2 == 0 else -1
            speed = random.uniform(2.2, 4.8) * direction
            craft = []
            n_craft = random.randint(1, 3)
            gap = W // (n_craft + 1)
            for j in range(n_craft):
                cx = j * gap + random.randint(40, 120)
                cw = random.randint(90, 160)
                craft.append([cx, y + 20, cw, 70, speed])
            self.lanes.append({"y": y, "craft": craft, "dir": direction})
        self.particles = []

    def hop(self, dx, dy):
        if not self.alive:
            return
        self.pvx = dx * 8
        self.pvy = dy * 8

    def update_player(self):
        if not self.alive:
            return
        self.px += self.pvx
        self.py += self.pvy
        self.pvx *= 0.85
        self.pvy *= 0.85
        self.px = max(40, min(W - 40, self.px))
        self.py = max(120, min(H - 120, self.py))
        progress = int((H - self.py) / 10)
        if progress > self.reached:
            self.score += (progress - self.reached) * 2
            self.reached = progress

    def update_lanes(self):
        for lane in self.lanes:
            for c in lane["craft"]:
                c[0] += c[4]
                if c[0] > W + 100:
                    c[0] = -c[2] - 20
                elif c[0] < -c[2] - 100:
                    c[0] = W + 20

    def check_collision(self):
        if not self.alive:
            return
        pr = pygame.Rect(self.px - 28, self.py - 28, 56, 56)
        for lane in self.lanes:
            for c in lane["craft"]:
                cr = pygame.Rect(c[0], c[1], c[2], c[3])
                if pr.colliderect(cr):
                    self.alive = False
                    self.score = max(0, self.score - 50)
                    for _ in range(20):
                        ang = random.random() * 6.28
                        self.particles.append([self.px, self.py, math.cos(ang)*8, math.sin(ang)*8, 30, ROSE])
                    return

    def autoplay(self):
        if not self.alive:
            if random.random() < 0.08:
                self.reset()
            return
        safe_up = True
        test_y = self.py - 90
        pr = pygame.Rect(self.px - 40, test_y - 40, 80, 80)
        nearby_threat = False
        for lane in self.lanes:
            for c in lane["craft"]:
                if abs(c[1] - self.py) < 100:
                    if abs(c[0] + c[2]/2 - self.px) < 180:
                        nearby_threat = True
                if abs(c[1] - test_y) < 70:
                    cr = pygame.Rect(c[0]-20, c[1], c[2]+40, c[3])
                    if pr.colliderect(cr):
                        safe_up = False
        if safe_up and self.py > 300 and random.random() < 0.55:
            self.hop(0, -1.2)
        elif nearby_threat:
            self.hop(random.choice([-1.5, 1.5]), 0)
        else:
            if random.random() < 0.5:
                self.hop(random.choice([-1, 1, 0]), random.choice([0, -0.6]))
            elif random.random() < 0.1:
                self.hop(0, 0.4)

    def update_particles(self):
        self.particles = [p for p in self.particles if p[4] > 0]
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.95
            p[3] *= 0.95
            p[4] -= 1

    def draw(self, surf):
        surf.fill(BG)
        for lane in self.lanes:
            y = lane["y"]
            pygame.draw.rect(surf, LANE_BG, (0, y, W, 120))
            pygame.draw.line(surf, CYAN, (0, y), (W, y), 3)
            pygame.draw.line(surf, MAG, (0, y + 120), (W, y + 120), 3)
            for c in lane["craft"]:
                col = GOLD if lane["dir"] > 0 else LIME
                pygame.draw.rect(surf, col, (c[0], c[1], c[2], c[3]), border_radius=12)
                pygame.draw.rect(surf, WHITE, (c[0]+8, c[1]+12, c[2]-16, 18), border_radius=6)
                pygame.draw.line(surf, CYAN, (c[0], c[1]+c[3]//2), (c[0]+c[2], c[1]+c[3]//2), 4)
        for p in self.particles:
            if p[4] > 0:
                pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), max(2, p[4]//6))
        if self.alive:
            pygame.draw.circle(surf, PLAYER_COL, (int(self.px), int(self.py)), 32)
            pygame.draw.circle(surf, WHITE, (int(self.px), int(self.py)), 18)
            pygame.draw.circle(surf, CYAN, (int(self.px)-8, int(self.py)-6), 6)
            pygame.draw.circle(surf, CYAN, (int(self.px)+8, int(self.py)-6), 6)
        else:
            pygame.draw.circle(surf, ROSE, (int(self.px), int(self.py)), 24)
        title = self.font_lg.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W//2, 70)))
        handle = self.font_sm.render(HANDLE, True, CYAN)
        surf.blit(handle, handle.get_rect(center=(W//2, 140)))
        sc = self.font.render(f"SCORE {self.score}", True, WHITE)
        surf.blit(sc, sc.get_rect(center=(W//2, H - 140)))
        status = "HOP THE TIDES" if self.alive else "ZAPPED — RESPWN"
        st = self.font_sm.render(status, True, LIME if self.alive else ROSE)
        surf.blit(st, st.get_rect(center=(W//2, H - 80)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        self.hop(0, -1)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        self.hop(0, 1)
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.hop(-1, 0)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.hop(1, 0)
                    elif ev.key == pygame.K_r:
                        self.reset()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.pvx -= 1.2
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.pvx += 1.2
            self.update_lanes()
            self.update_player()
            self.check_collision()
            self.update_particles()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-movflags", "+faststart", "-an", OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.update_lanes()
                self.update_player()
                self.check_collision()
                self.update_particles()
                self.draw(canvas)
                raw = pygame.image.tostring(canvas, "RGB")
                proc.stdin.write(raw)
                if i % 30 == 0:
                    print(f"frame {i}/{frames} score={self.score}")
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
            if rc != 0:
                raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
            print("wrote", OUT)
        except Exception as e:
            proc.kill()
            raise
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
