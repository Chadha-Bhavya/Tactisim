from dataclasses import dataclass
from enum import Enum
from typing import List, Union


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float


@dataclass(frozen=True)
class Pitch:
    length: float = 105.0
    width: float = 68.0


@dataclass(frozen=True)
class Ball:
    pos: Vec2
    carrier_id: str


@dataclass(frozen=True)
class OutfieldAttributes:
    pace: int
    defending: int
    physicality: int
    shooting: int
    dribbling: int
    passing: int


@dataclass(frozen=True)
class GKAttributes:
    ball_control: int
    shot_saving: int
    pace: int
    passing_short: int
    passing_long: int


@dataclass(frozen=True)
class Player:
    id: str
    team_id: str
    is_gk: bool
    pos: Vec2
    attrs: Union[OutfieldAttributes, GKAttributes]



class Objective(str, Enum):
    WIN_GAME = "WIN_GAME"
    PROTECT_LEAD = "PROTECT_LEAD"


@dataclass(frozen=True)
class Context:
    minute: int
    my_goals: int
    opp_goals: int
    objective: Objective


@dataclass(frozen=True)
class Constraints:
    max_move_outfield: float = 8.0
    min_spacing: float = 1.5
    gk_max_x: float = 20.0
    gk_min_y: float = 13.84
    gk_max_y: float = 54.16


@dataclass(frozen=True)
class Scenario:
    pitch: Pitch
    my_players: List[Player]
    opp_players: List[Player]
    ball: Ball
    context: Context
    constraints: Constraints


@dataclass(frozen=True)
class PlayerRecommendation:
    player_id: str
    new_x: float
    new_y: float
    dx: float
    dy: float
    instruction: str  # MOVE or HOLD


@dataclass(frozen=True)
class RunResult:
    recommendations: List[PlayerRecommendation]
    team_score: float
    reasoning: List[str]

