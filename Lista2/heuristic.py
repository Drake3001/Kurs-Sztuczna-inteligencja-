from random import random 
from typing import Callable


HeuristicT = Callable[[list[list[str]], str, str, int], float]


def sprinter_heuristic(state: list[list[str]], side: str, opponent: str, direction: int) -> float: 

    y_size = len(state)
    my_max_advancement = 0
    enemy_max_advancement = 0
    
    for y, row in enumerate(state):
        for cell in row:
            if cell == side:
                advancement = y if direction == 1 else (y_size - 1 - y)
                my_max_advancement = max(my_max_advancement, advancement)
            elif cell == opponent:
                advancement = y if direction == -1 else (y_size - 1 - y)
                enemy_max_advancement = max(enemy_max_advancement, advancement)
                
    return float(my_max_advancement - enemy_max_advancement) * 0.1


def material_heuristic(state: list[list[str]], side: str, opponent: str, direction: int) -> float:
    my_pieces = 0
    enemy_pieces = 0
    
    for row in state:
        for cell in row:
            if cell == side:
                my_pieces += 1
            elif cell == opponent:
                enemy_pieces += 1
                
    return float(my_pieces - enemy_pieces)


def phalanx_heuristic(state: list[list[str]], side: str, opponent: str, direction: int) -> float:
    score = 0.0
    y_size = len(state)
    x_size = len(state[0])

    for y in range(y_size):
        for x in range(x_size):
            if state[y][x] == side:
                back_y = y - direction 
                if 0 <= back_y < y_size:
                    if x > 0 and state[back_y][x-1] == side:
                        score += 1.0
                    if x < x_size - 1 and state[back_y][x+1] == side:
                        score += 1.0
                        
            elif state[y][x] == opponent:
                back_y = y + direction 
                if 0 <= back_y < y_size:
                    if x > 0 and state[back_y][x-1] == opponent:
                        score -= 1.0
                    if x < x_size - 1 and state[back_y][x+1] == opponent:
                        score -= 1.0
                        
    return score * 0.2

def center_control_heuristic(state: list[list[str]], side: str, opponent: str, direction: int) -> float:
    score = 0.0
    x_size = len(state[0])
    
    center_left = x_size // 2 - 1
    center_right = x_size // 2

    for y, row in enumerate(state):
        for x, cell in enumerate(row):
            weight = 0.0
            if x == center_left or x == center_right:
                weight = 2.0
            elif x == center_left - 1 or x == center_right + 1:
                weight = 1.0
                
            if cell == side:
                score += weight
            elif cell == opponent:
                score -= weight
                
    return score * 0.1


def passed_pawn_heuristic(state: list[list[str]], side: str, opponent: str, direction: int) -> float:
    score = 0.0
    y_size = len(state)
    x_size = len(state[0])

    for y in range(y_size):
        for x in range(x_size):
            cell = state[y][x]
            
            if cell == side:
                is_passed = True
                rows_ahead = range(y + 1, y_size) if direction == 1 else range(y - 1, -1, -1)
                
                for ahead_y in rows_ahead:
                    for ahead_x in [x - 1, x, x + 1]:
                        if 0 <= ahead_x < x_size:
                            if state[ahead_y][ahead_x] == opponent:
                                is_passed = False
                                break 
                    if not is_passed: break
                
                if is_passed:
                    advancement = y if direction == 1 else (y_size - 1 - y)
                    score += 0.5 + (advancement * 0.2)

            elif cell == opponent:
                is_passed = True
                opp_direction = -direction
                rows_ahead = range(y + 1, y_size) if opp_direction == 1 else range(y - 1, -1, -1)
                
                for ahead_y in rows_ahead:
                    for ahead_x in [x - 1, x, x + 1]:
                        if 0 <= ahead_x < x_size:
                            if state[ahead_y][ahead_x] == side:
                                is_passed = False
                                break
                    if not is_passed: break
                
                if is_passed:
                    advancement = y if opp_direction == 1 else (y_size - 1 - y)
                    score -= 0.5 + (advancement * 0.2)

    return score


def heuristic_factory(weights: list[float]) -> HeuristicT:
    early_mat_w, early_sprint_w, early_phal_w, early_center_w, early_passed_w, \
    mid_mat_w, mid_sprint_w, mid_phal_w, mid_center_w, mid_passed_w, \
    late_mat_w, late_sprint_w, late_phal_w, late_center_w, late_passed_w = weights
    
    def adaptive_heuristic(state: list[list[str]], side: str, opponent: str, direction: int) -> float:
        my_pieces = 0
        enemy_pieces = 0
        for row in state:
            for cell in row:
                if cell == side: my_pieces += 1
                elif cell == opponent: enemy_pieces += 1
                
        total_pieces = my_pieces + enemy_pieces
        starting_pieces = 4 * len(state[0])

        material_score = material_heuristic(state, side, opponent, direction)
        sprinter_score = sprinter_heuristic(state, side, opponent, direction)
        phalanx_score = phalanx_heuristic(state, side, opponent, direction)
        center_score = center_control_heuristic(state, side, opponent, direction)
        passed_score = passed_pawn_heuristic(state, side, opponent, direction)

        if total_pieces > 0.70 * starting_pieces:
            return (material_score * early_mat_w + sprinter_score * early_sprint_w + 
                    phalanx_score * early_phal_w + center_score * early_center_w + passed_score * early_passed_w)
        elif total_pieces > 0.40 * starting_pieces:
            return (material_score * mid_mat_w + sprinter_score * mid_sprint_w + 
                    phalanx_score * mid_phal_w + center_score * mid_center_w + passed_score * mid_passed_w)
        else:
            return (material_score * late_mat_w + sprinter_score * late_sprint_w + 
                    phalanx_score * late_phal_w + center_score * late_center_w + passed_score * late_passed_w)
    return adaptive_heuristic


def random_heuristic(state: list[list[str]], side: str, opponent: str, direction: int)-> float:
    return (random() - 0.5) * 0.1