from math import hypot
from .models import Vec2, Pitch


def dist(a: Vec2, b: Vec2) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def dist_sq(a: Vec2, b: Vec2) -> float:
    dx = a.x - b.x
    dy = a.y - b.y
    return dx * dx + dy * dy


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


def round_1dp(v: float) -> float:
    return round(v, 1)


def in_bounds(pos: Vec2, pitch: Pitch) -> bool:
    return 0.0 <= pos.x <= pitch.length and 0.0 <= pos.y <= pitch.width
