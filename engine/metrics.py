from .models import Player, Scenario
from .utils import dist_sq

def horizontal_compactness(players):
    """
    Calculates the team's width across the pitch (how wide from sideline to sideline).
    """
    outfielder_y_coords = [p.pos.y for p in players if not p.is_gk]
    if not outfielder_y_coords:
        return 0.0
        
    current_width = max(outfielder_y_coords) - min(outfielder_y_coords)
    
    LIMIT_DISCONNECTED = 40.0
    LIMIT_OVERLY_SQUEEZED = 20.0
    ELITE_RANGE_START = 25.0
    ELITE_RANGE_END = 30.0

    if current_width <= LIMIT_OVERLY_SQUEEZED or current_width >= LIMIT_DISCONNECTED:
        return 0.0
    if ELITE_RANGE_START <= current_width <= ELITE_RANGE_END:
        return 1.0
    
    if current_width < ELITE_RANGE_START:
        return (current_width - LIMIT_OVERLY_SQUEEZED) / (ELITE_RANGE_START - LIMIT_OVERLY_SQUEEZED)
    
    return (LIMIT_DISCONNECTED - current_width) / (LIMIT_DISCONNECTED - ELITE_RANGE_END)


def vertical_compactness(players):
    """
    Calculates the distance between the team's highest and lowest outfielders(team depth).
    """
    outfielder_x_coords = [p.pos.x for p in players if not p.is_gk]
    if not outfielder_x_coords:
        return 0.0
    
    current_depth = max(outfielder_x_coords) - min(outfielder_x_coords)
    
    LIMIT_TOTAL_FAILURE = 55.0
    LIMIT_TOO_NARROW = 30.0
    PERFECT_RANGE_START = 35.0
    PERFECT_RANGE_END = 45.0

    if current_depth <= LIMIT_TOO_NARROW or current_depth >= LIMIT_TOTAL_FAILURE:
        return 0.0
    if PERFECT_RANGE_START <= current_depth <= PERFECT_RANGE_END:
        return 1.0
    
    if current_depth < PERFECT_RANGE_START:
        return (current_depth - LIMIT_TOO_NARROW) / (PERFECT_RANGE_START - LIMIT_TOO_NARROW)
    
    return (LIMIT_TOTAL_FAILURE - current_depth) / (LIMIT_TOTAL_FAILURE - PERFECT_RANGE_END)

def press_access(players, ball, k_nearest=3):
    """
    Evaluates how effectively the nearest players can close down the ball carrier.
    Factors in travel time, physical strength, and tactical position.
    """
    sq_distances_to_ball = [(dist_sq(p.pos, ball.pos), p) for p in players if not p.is_gk]
    sq_distances_to_ball.sort(key=lambda x: x[0])
    top_candidates = sq_distances_to_ball[:k_nearest]

    effective_pressing_times = []
    
    for distance_sq, player in top_candidates:
        actual_distance = distance_sq ** 0.5
        travel_speed = max(1.0, player.attrs.pace)
        raw_reach_time = actual_distance / travel_speed
        
        ball_winning_strength = (player.attrs.defending + player.attrs.physicality) / 10.0
        
        if player.pos.x > 70.0:
            tactical_bonus = 1.2 # Forward press is high value
        elif player.pos.x > 35.0:
            tactical_bonus = 1.0
        else:
            tactical_bonus = 0.8 # Defender leaving line is risky
            
        effective_time = raw_reach_time / (ball_winning_strength * tactical_bonus)
        effective_pressing_times.append(effective_time)
        
    if not effective_pressing_times:
        return 0.0
        
    best_reach_time = min(effective_pressing_times)
    
    if best_reach_time <= 2.0:
        return 1.0
    if best_reach_time >= 6.0:
        return 0.0
    return (6.0 - best_reach_time) / 4.0

def line_height_risk(my_players, opp_players):
    """
    Assesses the danger of the defensive line being bypassed by fast attackers.
    Incorporates offside rules, the halfway line, and covering speed.
    """
    outfield_defenders = [p for p in my_players if not p.is_gk]
    if not outfield_defenders:
        return 0.0
    
    outfield_defenders.sort(key=lambda p: p.pos.x)
    deepest_three_defenders = outfield_defenders[:3]
    offside_line_x = outfield_defenders[0].pos.x 
    
    peak_recovery_strength = max(
        (d.attrs.pace * 0.8 + d.attrs.defending * 0.1 + d.attrs.physicality * 0.1)
        for d in deepest_three_defenders
    )

    HALFWAY_LINE_X = 52.5 
    legal_threats = [
        p for p in opp_players 
        if not p.is_gk and (p.pos.x >= offside_line_x or p.pos.x >= HALFWAY_LINE_X)
    ]
    
    if not legal_threats:
        return 1.0 

    legal_threats.sort(key=lambda p: p.pos.x)
    highest_attacker_threat = max(
        (att.attrs.pace * 0.95 + (1.0 - att.pos.x / 105.0) * 0.05)
        for att in legal_threats[:3]
    )

    danger_ratio = (highest_attacker_threat / max(1.0, peak_recovery_strength))
    height_penalty = (offside_line_x / 40.0)
    total_risk = danger_ratio * height_penalty
    
    return max(0.0, 1.0 - min(total_risk, 1.0))

def ball_side_shift(players, ball, pitch_width=68.0):
    """
    Measures how well the defensive block slides laterally toward the ball side.
    Rewards 'tucking in' to protect the center while funneling play wide.
    """
    outfielders = [p for p in players if not p.is_gk]
    if not outfielders:
        return 0.0
        
    outfielders.sort(key=lambda p: p.pos.x)
    active_defensive_block = outfielders[:8]
    
    sorted_y_positions = sorted([p.pos.y for p in active_defensive_block])
    num_players = len(sorted_y_positions)
    mid_index = num_players // 2
    block_median_y = (sorted_y_positions[mid_index - 1] + sorted_y_positions[mid_index]) / 2.0

    pitch_center_y = pitch_width / 2.0
    tucked_target_y = ball.pos.y + (pitch_center_y - ball.pos.y) * 0.2
    
    shift_distance_error = abs(block_median_y - tucked_target_y)
    
    if shift_distance_error <= 3.0:
        return 1.0
    if shift_distance_error >= 15.0:
        return 0.0
    
    return (15.0 - shift_distance_error) / 12.0

def weighted_score(scenario: Scenario, players):
    """
    Combines all individual metrics into a single score out of 100.
    Adjusts the importance of each metric based on the match objective.
    """
    metric_results = {
        "width": horizontal_compactness(players),
        "depth": vertical_compactness(players),
        "press": press_access(players, scenario.ball),
        "risk": line_height_risk(players, scenario.opp_players),
        "shift": ball_side_shift(players, scenario.ball, scenario.pitch.width),
    }

    if scenario.context.objective == "WIN_GAME":
        weights = {"press": 0.30, "depth": 0.20, "shift": 0.20, "width": 0.15, "risk": 0.15}
    else: # PROTECT_LEAD
        weights = {"risk": 0.30, "width": 0.25, "depth": 0.25, "shift": 0.15, "press": 0.05}

    final_weighted_sum = sum(metric_results[k] * weights[k] for k in weights)
    return round(final_weighted_sum * 100.0, 1)