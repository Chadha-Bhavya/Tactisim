from dataclasses import dataclass
from .models import Player, Scenario, Vec2
from .utils import dist, clamp, round_1dp, in_bounds
from .metrics import weighted_score


SHIFT_STEP = 3.0
PRESS_STEP = 4.0
WIDTH_COMPRESS_FACTOR = 0.85
DEPTH_COMPRESS_FACTOR = 0.85
BALL_SHIFT_STRENGTH = 0.3


@dataclass
class Candidate:
    players: list[Player]
    score: float
    depth: int


def _valid(base, cand, s: Scenario):
    """Validates candidate against movement limits, spacing, bounds, and GK zone."""
    base_map = {p.id: p for p in base}
    c = s.constraints

    gk = next((p for p in cand if p.is_gk), None)
    if gk and (gk.pos.x > c.gk_max_x or not (c.gk_min_y <= gk.pos.y <= c.gk_max_y)):
        return False

    for i, p in enumerate(cand):
        if not p.is_gk and dist(p.pos, base_map[p.id].pos) > c.max_move_outfield:
            return False
        if not in_bounds(p.pos, s.pitch):
            return False
        for j in range(i + 1, len(cand)):
            if dist(p.pos, cand[j].pos) < c.min_spacing:
                return False
    return True


def _make_player(p: Player, new_x: float, new_y: float) -> Player:
    """Creates a new player with updated position."""
    return Player(p.id, p.team_id, p.is_gk, Vec2(round_1dp(new_x), round_1dp(new_y)), p.attrs)


def shift_vertical(players, dx, pitch):
    """Moves entire team forward or backward along the x-axis."""
    return [
        _make_player(p, clamp(p.pos.x + dx, 0, pitch.length), p.pos.y)
        for p in players
    ]


def shift_lateral(players, dy, pitch):
    """Slides entire team left or right along the y-axis."""
    return [
        _make_player(p, p.pos.x, clamp(p.pos.y + dy, 0, pitch.width))
        for p in players
    ]


def shift_toward_ball(players, ball, pitch):
    """Shifts defensive block laterally toward the ball's y-position."""
    pitch_center = pitch.width / 2
    target_offset = (ball.pos.y - pitch_center) * BALL_SHIFT_STRENGTH
    return [
        _make_player(p, p.pos.x, clamp(p.pos.y + target_offset, 0, pitch.width))
        if not p.is_gk else p
        for p in players
    ]


def compress_width(players, pitch):
    """Moves wide players toward the center of the pitch."""
    center_y = pitch.width / 2
    return [
        _make_player(p, p.pos.x, center_y + (p.pos.y - center_y) * WIDTH_COMPRESS_FACTOR)
        if not p.is_gk else p
        for p in players
    ]


def compress_depth(players):
    """Pulls team closer together vertically around the team's center."""
    outfielders = [p for p in players if not p.is_gk]
    if not outfielders:
        return players
    
    team_center_x = sum(p.pos.x for p in outfielders) / len(outfielders)
    return [
        _make_player(p, team_center_x + (p.pos.x - team_center_x) * DEPTH_COMPRESS_FACTOR, p.pos.y)
        if not p.is_gk else p
        for p in players
    ]


def press_nearest(players, ball):
    """Moves the nearest outfielder toward the ball carrier."""
    outfielders = [(p, dist(p.pos, ball.pos)) for p in players if not p.is_gk]
    if not outfielders:
        return players
    
    target = min(outfielders, key=lambda x: x[1])[0]
    result = []
    
    for p in players:
        if p.id != target.id:
            result.append(p)
        else:
            dx = ball.pos.x - p.pos.x
            dy = ball.pos.y - p.pos.y
            mag = (dx * dx + dy * dy) ** 0.5 or 1
            result.append(_make_player(p, p.pos.x + dx / mag * PRESS_STEP, p.pos.y + dy / mag * PRESS_STEP))
    
    return result


def adjust_back_line(players, dx, pitch):
    """Moves the four deepest outfielders forward or backward."""
    outfielders = sorted([p for p in players if not p.is_gk], key=lambda p: p.pos.x)
    back_four_ids = {p.id for p in outfielders[:4]} if len(outfielders) >= 4 else {p.id for p in outfielders}
    
    return [
        _make_player(p, clamp(p.pos.x + dx, 0, pitch.length), p.pos.y)
        if p.id in back_four_ids else p
        for p in players
    ]


def _generate_candidates(players, scenario):
    """Generates all candidate formations from 10 tactical transformations."""
    s = scenario
    return [
        shift_vertical(players, SHIFT_STEP, s.pitch),
        shift_vertical(players, -SHIFT_STEP, s.pitch),
        shift_lateral(players, SHIFT_STEP, s.pitch),
        shift_lateral(players, -SHIFT_STEP, s.pitch),
        shift_toward_ball(players, s.ball, s.pitch),
        compress_width(players, s.pitch),
        compress_depth(players),
        press_nearest(players, s.ball),
        adjust_back_line(players, SHIFT_STEP, s.pitch),
        adjust_back_line(players, -SHIFT_STEP, s.pitch),
    ]


def beam_search_realtime(scenario: Scenario):
    """Fast beam search for real-time recommendations. Width=4, Depth=2."""
    return _beam_search(scenario, beam_width=4, depth=2)


def beam_search_deep(scenario: Scenario):
    """Thorough beam search for deep analysis. Width=8, Depth=3."""
    return _beam_search(scenario, beam_width=8, depth=3)


def _beam_search(scenario: Scenario, beam_width: int, depth: int):
    """Core beam search that tracks best formation across all depths."""
    base = scenario.my_players
    base_score = weighted_score(scenario, base)
    
    best_players = base
    best_score = base_score
    
    beam = [(base_score, base)]
    
    for current_depth in range(1, depth + 1):
        all_candidates = []
        
        for _, players in beam:
            candidates = _generate_candidates(players, scenario)
            
            for cand in candidates:
                if _valid(base, cand, scenario):
                    score = weighted_score(scenario, cand)
                    all_candidates.append((score, cand))
                    
                    if score > best_score:
                        best_score = score
                        best_players = cand
        
        all_candidates.sort(key=lambda x: -x[0])
        beam = all_candidates[:beam_width]
        
        if not beam:
            break
    
    return best_players, best_score
