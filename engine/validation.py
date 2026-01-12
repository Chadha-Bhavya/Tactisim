from .models import Scenario


def _validate_attrs(attrs):
    for v in vars(attrs).values():
        if not isinstance(v, int) or not (1 <= v <= 5):
            raise ValueError("Attributes must be integers in [1,5]")


def validate_scenario(s: Scenario) -> None:
    if len(s.my_players) != 11 or len(s.opp_players) != 11:
        raise ValueError("Must be exactly 11v11")

    if sum(p.is_gk for p in s.my_players) != 1:
        raise ValueError("User team must have exactly one GK")

    if sum(p.is_gk for p in s.opp_players) != 1:
        raise ValueError("Opponent team must have exactly one GK")

    opp_ids = {p.id for p in s.opp_players}
    if s.ball.carrier_id not in opp_ids:
        raise ValueError("Ball carrier must be opponent player")

    if not (0 <= s.context.minute <= 90):
        raise ValueError("Minute must be between 0 and 90")

    for p in s.my_players + s.opp_players:
        _validate_attrs(p.attrs)

    gk = next(p for p in s.my_players if p.is_gk)
    c = s.constraints
    if gk.pos.x > c.gk_max_x or not (c.gk_min_y <= gk.pos.y <= c.gk_max_y):
        raise ValueError("GK out of allowed zone")
