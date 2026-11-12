#!/usr/bin/env python3
"""Procedurally synthesise the game's audio (ambience, machine loops, UI sfx) -> assets/audio/*.wav

    .venv/bin/python tools/gen_audio.py

Everything is generated from noise and oscillators so there are no licensing concerns.
Loops are made seamless by cross-fading the tail into the head.
"""
import os
import wave

import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
rng = np.random.default_rng(7)


def t_axis(sec):
    return np.arange(int(SR * sec)) / SR


def white(sec):
    return rng.standard_normal(int(SR * sec))


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    b = 1 - a
    for i in range(len(x)):
        acc = b * x[i] + a * acc
        y[i] = acc
    return y


def fft_filter(x, lo=None, hi=None, slope=1.0):
    """Brick-ish band filter in the frequency domain with soft edges."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** (4 * slope))
    if hi:
        g *= 1 / (1 + (f / hi) ** (4 * slope))
    return np.fft.irfft(X * g, n=len(x))


def brown(sec):
    x = np.cumsum(white(sec))
    x = fft_filter(x, lo=20)
    return x / (np.abs(x).max() + 1e-9)


def pink(sec):
    X = np.fft.rfft(white(sec))
    f = np.fft.rfftfreq(int(SR * sec), 1 / SR)
    X /= np.sqrt(np.maximum(f, 1.0))
    x = np.fft.irfft(X, n=int(SR * sec))
    return x / (np.abs(x).max() + 1e-9)


def norm(x, peak=0.8):
    return x / (np.abs(x).max() + 1e-9) * peak


def env(n, a=0.002, d=0.2, sus=0.0, curve=4.0):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-6), np.exp(-(t - a) * curve / max(d, 1e-6)))
    return np.maximum(e, sus)


def seamless(x, fade=1.0):
    """Cross-fade the last `fade` seconds into the beginning so the clip loops cleanly."""
    n = int(SR * fade)
    head, body, tail = x[:n], x[n:-n] if len(x) > 2 * n else x[n:], x[-n:]
    w = np.linspace(0, 1, n)
    start = head * w + tail * (1 - w)
    return np.concatenate([start, x[n:-n]])


def write(name, x, stereo_width=0.0):
    os.makedirs(OUT, exist_ok=True)
    x = np.clip(x, -1, 1)
    if stereo_width > 0:
        d = int(SR * 0.011)
        r = np.roll(x, d)
        data = np.stack([x, x * (1 - stereo_width) + r * stereo_width], axis=1)
    else:
        data = np.stack([x, x], axis=1)
    pcm = (data * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", name, f"{len(x) / SR:.1f}s")


def metal_hit(freqs=(523, 1287, 2210, 3301), dec=(0.6, 0.35, 0.25, 0.15), sec=1.2, noise=0.3):
    t = t_axis(sec)
    y = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / d) / (i + 1)
            for i, (f, d) in enumerate(zip(freqs, dec)))
    y += fft_filter(white(sec), lo=1500) * np.exp(-t / 0.02) * noise
    return y


# ------------------------------------------------------------------ ambience
def ambience(sec=40.0):
    t = t_axis(sec)
    rumble = fft_filter(brown(sec), hi=180) * 0.9
    hum = (np.sin(2 * np.pi * 50 * t) * 0.25 + np.sin(2 * np.pi * 100 * t) * 0.12 + np.sin(2 * np.pi * 150 * t) * 0.05)
    hum *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t)
    air = fft_filter(pink(sec), lo=300, hi=3000) * 0.08
    x = rumble + hum * 0.35 + air
    # distant clanks / impacts with hall reverb tail
    for _ in range(int(sec * 0.6)):
        at = rng.uniform(0, sec - 2)
        f0 = rng.uniform(300, 900)
        hit = metal_hit((f0, f0 * 2.43, f0 * 4.1), (0.5, 0.3, 0.15), 1.6, 0.4)
        hit = fft_filter(hit, hi=2500) * rng.uniform(0.05, 0.16)
        i = int(at * SR)
        x[i:i + len(hit)] += hit[: len(x) - i]
    # occasional steam vent
    for _ in range(int(sec / 12)):
        at = rng.uniform(0, sec - 4)
        n = int(SR * 3)
        e = np.sin(np.linspace(0, np.pi, n)) ** 2
        v = fft_filter(white(3), lo=1500, hi=8000) * e * 0.05
        i = int(at * SR)
        x[i:i + n] += v[: len(x) - i]
    x = hall(x, 0.25)
    return norm(seamless(x, 2.0), 0.6)


def hall(x, mix=0.3):
    """Cheap feedback-delay reverb for big industrial halls."""
    y = x.copy()
    for d, g in ((0.043, 0.5), (0.071, 0.45), (0.113, 0.4), (0.167, 0.35), (0.241, 0.3)):
        n = int(SR * d)
        z = np.zeros_like(x)
        z[n:] = x[:-n] * g
        z = onepole_lp(z, 2500) if len(z) < SR * 60 else z
        y += z * mix
    return y


# ------------------------------------------------------------------ machine loops (positional)
def loop_drill(sec=6.0):
    t = t_axis(sec)
    rot = 0.5 + 0.5 * np.sin(2 * np.pi * 3.0 * t) ** 2   # 3 Hz chatter (integer loops in 6 s)
    x = fft_filter(brown(sec), lo=40, hi=400) * rot
    x += np.sin(2 * np.pi * 90 * t + 0.6 * np.sin(2 * np.pi * 3 * t)) * 0.25
    x += fft_filter(white(sec), lo=1200, hi=4000) * 0.06 * rot
    return norm(seamless(x, 0.5), 0.7)


def loop_furnace(sec=6.0):
    t = t_axis(sec)
    flutter = 0.7 + 0.3 * fft_filter(white(sec), hi=6) / 0.05
    x = fft_filter(pink(sec), lo=60, hi=900) * np.clip(flutter, 0.3, 1.3)
    x += fft_filter(brown(sec), hi=120) * 0.5
    # crackles
    for _ in range(40):
        i = rng.integers(0, int(SR * sec) - 2000)
        c = fft_filter(white(0.04), lo=2000) * np.exp(-np.arange(int(SR * 0.04)) / 200) * rng.uniform(0.1, 0.4)
        x[i:i + len(c)] += c
    return norm(seamless(x, 0.5), 0.7)


def loop_hum(sec=4.0):
    t = t_axis(sec)
    x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((60, 0.5), (120, 0.35), (180, 0.15), (240, 0.1), (360, 0.05)))
    x *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.5 * t)
    x += fft_filter(white(sec), lo=2000, hi=9000) * 0.02
    return norm(seamless(x, 0.3), 0.5)


def loop_press(sec=3.0):
    t = t_axis(sec)
    x = fft_filter(brown(sec), hi=200) * 0.25
    for k in range(2):  # two stamps per loop
        at = 0.4 + k * 1.5
        i = int(at * SR)
        n = int(SR * 0.6)
        thump = np.sin(2 * np.pi * 55 * np.arange(n) / SR) * np.exp(-np.arange(n) / (SR * 0.08))
        clank = metal_hit((410, 1030, 1870), (0.25, 0.15, 0.08), 0.6, 0.6)[:n]
        x[i:i + n] += thump * 0.9 + clank * 0.4
        # hydraulic hiss on return
        j = int((at + 0.55) * SR)
        m = int(SR * 0.5)
        hs = fft_filter(white(0.5), lo=2500, hi=7000) * np.sin(np.linspace(0, np.pi, m)) * 0.12
        x[j:j + m] += hs[: len(x) - j]
    return norm(x, 0.8)


def loop_steam(sec=5.0):
    t = t_axis(sec)
    x = fft_filter(white(sec), lo=900, hi=9000) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * t) ** 2)
    x += fft_filter(brown(sec), hi=150) * 0.3
    return norm(seamless(x, 0.5), 0.5)


def loop_turbine(sec=4.0):
    t = t_axis(sec)
    f = 380 + 6 * np.sin(2 * np.pi * 0.25 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * 0.3 + np.sin(ph * 2.01) * 0.12 + np.sin(ph * 3.02) * 0.06
    x += fft_filter(pink(sec), lo=200, hi=2500) * 0.35
    return norm(seamless(x, 0.4), 0.6)


def loop_bubbling(sec=5.0):
    """Chemical plants / refineries: churning liquid + pumps."""
    x = fft_filter(brown(sec), lo=40, hi=300) * 0.6
    for _ in range(140):
        i = rng.integers(0, int(SR * sec) - 4000)
        f = rng.uniform(250, 900)
        n = int(SR * rng.uniform(0.02, 0.06))
        tt = np.arange(n) / SR
        b = np.sin(2 * np.pi * (f + 1800 * tt) * tt) * np.exp(-tt * 60) * rng.uniform(0.1, 0.3)
        x[i:i + n] += b
    return norm(seamless(x, 0.5), 0.6)


def loop_servo(sec=4.0):
    """Assemblers / robot arms: servo whines and small clicks."""
    t = t_axis(sec)
    x = fft_filter(brown(sec), hi=200) * 0.25
    for k in range(4):
        st = k * 1.0 + 0.1
        n = int(SR * 0.55)
        tt = np.arange(n) / SR
        f = 900 + 500 * np.sin(np.pi * tt / 0.55)
        w = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.55) * 0.18
        i = int(st * SR)
        x[i:i + n] += w
        c = metal_hit((1800, 3200), (0.03, 0.02), 0.08, 0.5)
        j = int((st + 0.6) * SR)
        x[j:j + len(c)] += c[: len(x) - j] * 0.5
    return norm(x, 0.6)


# ------------------------------------------------------------------ UI / events
def sfx_click():
    n = int(SR * 0.05)
    x = fft_filter(white(0.05), lo=1500, hi=6000) * np.exp(-np.arange(n) / (SR * 0.006))
    return norm(x, 0.5)


def sfx_build():
    x = metal_hit((180, 433, 812, 1500), (0.4, 0.25, 0.15, 0.1), 0.9, 0.8)
    n = len(x)
    thump = np.sin(2 * np.pi * 70 * np.arange(n) / SR) * np.exp(-np.arange(n) / (SR * 0.09))
    return norm(hall(x * 0.5 + thump, 0.2), 0.8)


def sfx_research():
    t = t_axis(1.6)
    x = np.zeros_like(t)
    for k, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        st = k * 0.09
        e = np.where(t > st, np.exp(-(t - st) / 0.5), 0)
        x += (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * e
    return norm(hall(x, 0.3), 0.6)


def sfx_coins():
    x = np.zeros(int(SR * 0.8))
    for k in range(4):
        h = metal_hit((2400 + k * 180, 5100 + k * 300), (0.12, 0.06), 0.4, 0.2)
        i = int(k * 0.06 * SR)
        x[i:i + len(h)] += h * (1 - k * 0.15)
    return norm(x, 0.5)


def sfx_alarm():
    t = t_axis(1.5)
    f = 600 + 250 * (np.sin(2 * np.pi * 1.5 * t) > 0)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3
    x = fft_filter(x, hi=2500) * np.minimum(1, (1.5 - t) * 4)
    return norm(hall(x, 0.3), 0.5)


def sfx_achievement():
    t = t_axis(2.2)
    x = np.zeros_like(t)
    for k, f in enumerate((392.0, 523.25, 659.25, 783.99, 1046.5)):
        st = k * 0.11
        e = np.where(t > st, np.exp(-(t - st) / 0.8), 0)
        x += np.sin(2 * np.pi * f * t) * e + 0.4 * metal_hit((f * 2.76,), (0.6,), 2.2, 0)[: len(t)] * (t > st)
    return norm(hall(x, 0.35), 0.6)


def main():
    write("ambience_hall", ambience(), 0.6)
    write("loop_drill", loop_drill())
    write("loop_furnace", loop_furnace())
    write("loop_hum", loop_hum())
    write("loop_press", loop_press())
    write("loop_steam", loop_steam())
    write("loop_turbine", loop_turbine())
    write("loop_bubbling", loop_bubbling())
    write("loop_servo", loop_servo())
    write("sfx_click", sfx_click())
    write("sfx_build", sfx_build())
    write("sfx_research", sfx_research())
    write("sfx_coins", sfx_coins())
    write("sfx_alarm", sfx_alarm())
    write("sfx_achievement", sfx_achievement())


if __name__ == "__main__":
    main()
