"""A cool-looking click counter button built with tkinter (no extra installs).

Run:  python3 click_counter.py

- Click the glowing button to count.
- Your total is saved, so it survives restarts.
- Press R to reset the count.
"""

import json
import math
import random
import tkinter as tk
from pathlib import Path

SAVE_FILE = Path(__file__).with_name(".click_count.json")

WIDTH, HEIGHT = 520, 420
BG = "#0f0f1a"
GRAD_LEFT = (255, 0, 128)    # hot pink
GRAD_RIGHT = (121, 40, 202)  # purple
BTN_W, BTN_H = 260, 76
BTN_CX, BTN_CY = WIDTH // 2, 300


def lerp_color(a, b, t):
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def brighten(rgb, amount):
    return tuple(min(255, int(c + (255 - c) * amount)) for c in rgb)


def load_count():
    try:
        return int(json.loads(SAVE_FILE.read_text())["count"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def save_count(count):
    try:
        SAVE_FILE.write_text(json.dumps({"count": count}))
    except OSError:
        pass


class ClickCounter:
    def __init__(self, root):
        self.root = root
        self.count = load_count()
        self.hover = False
        self.pressed = False
        self.scale = 1.0
        self.pulse = 0.0
        self.particles = []
        self.count_bump = 0.0

        root.title("Click Counter")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG,
                                highlightthickness=0)
        self.canvas.pack()

        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        root.bind("<KeyPress-r>", self.reset)
        root.bind("<KeyPress-R>", self.reset)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tick()

    # ---------- input ----------
    def inside_button(self, x, y):
        w, h = BTN_W * self.scale, BTN_H * self.scale
        r = h / 2
        dx = max(abs(x - BTN_CX) - (w / 2 - r), 0)
        dy = y - BTN_CY
        return dx * dx + dy * dy <= r * r

    def on_motion(self, event):
        self.hover = self.inside_button(event.x, event.y)
        self.canvas.configure(cursor="hand2" if self.hover else "")

    def on_press(self, event):
        if self.inside_button(event.x, event.y):
            self.pressed = True

    def on_release(self, event):
        if self.pressed and self.inside_button(event.x, event.y):
            self.click()
        self.pressed = False

    def click(self):
        self.count += 1
        self.count_bump = 1.0
        save_count(self.count)
        for _ in range(28):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 9)
            self.particles.append({
                "x": BTN_CX, "y": BTN_CY,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 2,
                "life": 1.0,
                "color": lerp_color(GRAD_LEFT, GRAD_RIGHT, random.random()),
                "size": random.uniform(3, 7),
            })

    def reset(self, _event=None):
        self.count = 0
        self.count_bump = 1.0
        save_count(self.count)

    def on_close(self):
        save_count(self.count)
        self.root.destroy()

    # ---------- animation loop ----------
    def tick(self):
        target = 0.92 if self.pressed else (1.06 if self.hover else 1.0)
        self.scale += (target - self.scale) * 0.25
        self.pulse = (self.pulse + 0.05) % (2 * math.pi)
        self.count_bump *= 0.85

        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.35
            p["life"] -= 0.03
        self.particles = [p for p in self.particles if p["life"] > 0]

        self.draw()
        self.root.after(16, self.tick)

    # ---------- drawing ----------
    def draw_pill(self, cx, cy, w, h, left, right, tag):
        """Draw a horizontally gradient-filled pill using vertical lines."""
        c = self.canvas
        r = h / 2
        x0 = cx - w / 2
        steps = int(w)
        for i in range(steps):
            x = x0 + i
            if x < x0 + r:
                dx = x0 + r - x
            elif x > x0 + w - r:
                dx = x - (x0 + w - r)
            else:
                dx = 0
            half = math.sqrt(max(r * r - dx * dx, 0))
            c.create_line(x, cy - half, x, cy + half,
                          fill=lerp_color(left, right, i / steps), tags=tag)

    def draw(self):
        c = self.canvas
        c.delete("all")

        # Title
        c.create_text(WIDTH / 2, 50, text="CLICK COUNTER",
                      fill="#8888aa", font=("Helvetica", 14, "bold"))

        # Big count with a little bump when it changes
        size = int(64 + 22 * self.count_bump)
        c.create_text(WIDTH / 2 + 3, 153, text=str(self.count),
                      fill="#2a0a3a", font=("Helvetica", size, "bold"))
        c.create_text(WIDTH / 2, 150, text=str(self.count),
                      fill="#ffffff", font=("Helvetica", size, "bold"))
        label = "click" if self.count == 1 else "clicks"
        c.create_text(WIDTH / 2, 210, text=label,
                      fill="#8888aa", font=("Helvetica", 13))

        # Glow halo (pulses, stronger on hover)
        glow_strength = 0.35 + 0.15 * math.sin(self.pulse) + (0.25 if self.hover else 0)
        for k in range(6, 0, -1):
            t = glow_strength * (1 - k / 7)
            col = tuple(int(15 + (GRAD_RIGHT[i] - 15) * t) for i in range(3))
            self.draw_pill(BTN_CX, BTN_CY, BTN_W * self.scale + k * 8,
                           BTN_H * self.scale + k * 8, col, col, "glow")

        # Drop shadow
        self.draw_pill(BTN_CX, BTN_CY + 6 * self.scale, BTN_W * self.scale,
                       BTN_H * self.scale, (8, 8, 14), (8, 8, 14), "shadow")

        # The button
        boost = 0.18 if self.hover and not self.pressed else 0
        self.draw_pill(BTN_CX, BTN_CY, BTN_W * self.scale, BTN_H * self.scale,
                       brighten(GRAD_LEFT, boost), brighten(GRAD_RIGHT, boost),
                       "button")

        # Glossy highlight on the top half
        hw, hh = BTN_W * self.scale * 0.86, BTN_H * self.scale * 0.32
        self.draw_pill(BTN_CX, BTN_CY - BTN_H * self.scale * 0.2, hw, hh,
                       brighten(GRAD_LEFT, 0.35), brighten(GRAD_RIGHT, 0.35),
                       "gloss")

        c.create_text(BTN_CX, BTN_CY + 2, text="CLICK ME",
                      fill="#ffffff",
                      font=("Helvetica", int(22 * self.scale), "bold"))

        # Particles
        for p in self.particles:
            s = p["size"] * p["life"]
            c.create_oval(p["x"] - s, p["y"] - s, p["x"] + s, p["y"] + s,
                          fill=p["color"], outline="")

        c.create_text(WIDTH / 2, HEIGHT - 18, text="press R to reset",
                      fill="#44445a", font=("Helvetica", 10))


def main():
    root = tk.Tk()
    ClickCounter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
