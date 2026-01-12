from .validation import validate_scenario
from .strategy import beam_search
from .models import RunResult, PlayerRecommendation
from .utils import round_1dp


def run_engine_v1(s):
    validate_scenario(s)
    best, score = beam_search(s)

    base = {p.id: p for p in s.my_players}
    recs=[]

    for p in best:
        bp = base[p.id]
        dx = round_1dp(p.pos.x - bp.pos.x)
        dy = round_1dp(p.pos.y - bp.pos.y)
        instr = "HOLD" if abs(dx)+abs(dy)<0.2 else "MOVE"
        recs.append(PlayerRecommendation(p.id,p.pos.x,p.pos.y,dx,dy,instr))

    return RunResult(
        recommendations=recs,
        team_score=score,
        reasoning=["Best defensive adjustment under objective"]
    )
