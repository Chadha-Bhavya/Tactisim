from .models import Player, Scenario
from .utils import dist


def horizontal_compactness(players):
    xs = [p.pos.x for p in players if not p.is_gk]
    if not xs:
        return 0.0
    
    w = max(xs) - min(xs)
    
    min_limit = 30.0   
    perfect_min = 35.0  
    perfect_max = 45.0  
    max_limit = 75.0    

 
    if w <= min_limit or w >= max_limit:
        return 0.0
    
    if perfect_min <= w <= perfect_max:
        return 1.0
    
    if w < perfect_min:
        return (w - min_limit) / (perfect_min - min_limit)
    
    return (max_limit - w) / (max_limit - perfect_max)

def vertical_compactness(players):
    
    ys = [p.pos.y for p in players if not p.is_gk]
    if not ys:
        return 0.0
        
    h = max(ys) - min(ys)
    
    min_limit = 20.0    
    perfect_min = 25.0  
    perfect_max = 30.0 
    max_limit = 40.0    

    if h <= min_limit or h >= max_limit:
        return 0.0
    
    if perfect_min <= h <= perfect_max:
        return 1.0
    
    if h < perfect_min:
        return (h - min_limit) / (perfect_min - min_limit)
    
    return (max_limit - h) / (max_limit - perfect_max)


def press_access(players, ball):
    best = float("inf")
    for p in players:
        if p.is_gk:
            continue
        speed = max(1.0, p.attrs.pace)
        t = dist(p.pos, ball.pos) / speed
        best = min(best, t)
    if best <= 2:
        return 1.0
    if best >= 6:
        return 0.0
    return (6 - best) / 4.0


def line_height_risk(my_players, opp_players):
    defenders = [p for p in my_players if not p.is_gk]
    line_x = min(p.pos.x for p in defenders)
    fastest_att = max(p.attrs.pace for p in opp_players if not p.is_gk)
    slowest_def = min(p.attrs.pace for p in defenders)
    risk = (line_x / 40.0) * (fastest_att / max(1.0, slowest_def))
    return max(0.0, 1.0 - min(risk / 2.0, 1.0))


def ball_side_shift(players, ball):
    cy = sum(p.pos.y for p in players if not p.is_gk) / 10
    d = abs(cy - ball.pos.y)
    if d <= 5:
        return 1.0
    if d >= 25:
        return 0.0
    return (25 - d) / 20.0


def weighted_score(s: Scenario, players):
    m = {
        "h": horizontal_compactness(players),
        "v": vertical_compactness(players),
        "press": press_access(players, s.ball),
        "line": line_height_risk(players, s.opp_players),
        "shift": ball_side_shift(players, s.ball),
    }

    if s.context.objective == "WIN_GAME":
        w = {"press":0.30,"v":0.20,"shift":0.20,"h":0.15,"line":0.15}
    else:
        w = {"line":0.30,"h":0.25,"v":0.25,"shift":0.15,"press":0.05}

    return round(sum(m[k]*w[k] for k in w) * 100.0, 1)
