import heapq
from dataclasses import dataclass
from .models import Player, Scenario, Vec2
from .utils import dist, clamp, round_1dp, in_bounds
from .metrics import weighted_score


@dataclass
class Candidate:
    players: list[Player]
    score: float


def _valid(base, cand, s: Scenario):
    bm = {p.id: p for p in base}
    c = s.constraints

    gk = next((p for p in cand if p.is_gk), None)
    if gk and (gk.pos.x > c.gk_max_x or not (c.gk_min_y <= gk.pos.y <= c.gk_max_y)):
        return False

    for i, p in enumerate(cand):
        if not p.is_gk and dist(p.pos, bm[p.id].pos) > c.max_move_outfield:
            return False
        if not in_bounds(p.pos, s.pitch):
            return False
        for j in range(i + 1, len(cand)):
            if dist(p.pos, cand[j].pos) < c.min_spacing:
                return False
    return True


def shift_team(players, dx, pitch):
    return [
        Player(p.id,p.team_id,p.is_gk,
               Vec2(round_1dp(clamp(p.pos.x+dx,0,pitch.length)),p.pos.y),
               p.attrs)
        for p in players
    ]


def press_nearest(players, ball, step):
    target = min((p for p in players if not p.is_gk),
                 key=lambda p: dist(p.pos, ball.pos))
    out=[]
    for p in players:
        if p.id!=target.id:
            out.append(p)
        else:
            vx=ball.pos.x-p.pos.x; vy=ball.pos.y-p.pos.y
            mag=(vx*vx+vy*vy)**0.5 or 1
            out.append(Player(
                p.id,p.team_id,False,
                Vec2(round_1dp(p.pos.x+vx/mag*step),
                     round_1dp(p.pos.y+vy/mag*step)),
                p.attrs))
    return out


def beam_search(s: Scenario, beam_k=8):
    base = s.my_players
    base_score = weighted_score(s, base)
    heap=[]

    actions=[
        lambda ps: shift_team(ps,3,s.pitch),
        lambda ps: shift_team(ps,-3,s.pitch),
        lambda ps: press_nearest(ps,s.ball,4)
    ]

    for fn in actions:
        cand = fn(base)
        if _valid(base,cand,s):
            sc = weighted_score(s,cand)
            heapq.heappush(heap,(-sc,Candidate(cand,sc)))

    best = base; best_score = base_score
    beam = heapq.nsmallest(beam_k, heap)

    for _,c in beam:
        for fn in actions:
            cand2 = fn(c.players)
            if _valid(base,cand2,s):
                sc = weighted_score(s,cand2)
                if sc > best_score:
                    best = cand2; best_score = sc

    return best, best_score
