from __future__ import annotations
from heuristic import HeuristicT
import random
class BasePlayer: 
    def __init__(self): 
        self.side: str = '' 
        self.opponent: str = ''
        self.direction: int = 0
        self.x: int = 0 
        self.y: int = 0 

    def make_move(self, state: list[list[str]]) -> list[list[str]]: 
        pass

    def handle_move(self, state: list[list[str]])-> tuple[int, int, int, int, str]:
        pass 
    
    def set_direction(self, dir: int):
        self.direction = dir

    def set_x_size(self, x: int): 
        self.x = x

    def set_y_size(self, y: int):
        self.y = y  

    def set_side(self, side: str): 
        self.side = side

    def set_opponent(self, opponent: str):
        self.opponent = opponent

    def get_side(self): 
        return self.side

    def print_state(self, state: list[list[str]]):
        print(f"\n--- Tura gracza: {self.side} ---")
        
        for i in range(len(state) - 1, -1, -1):
            row = state[i]
            print(f"{i:>2} | " + " ".join(f"{cell:>2}" for cell in row))

        print("-" * (self.x * 3 + 4))
        print("     " + " ".join(f"{i:>2}" for i in range(self.x)))
        print()

    def reset_state(self): 
        pass 

    def get_match_stats(self) -> dict[str, object]:
        return {}


class CPlayer(BasePlayer): 
    def __init__(self): 
        super().__init__()
        self.heuristic = None
        self.heuristic_name: str = '' 
        self.search_depth: int = 0
        self.alfa_beta: bool = False
        self.positions_evaluated: int = 0

    def set_positions_evaluated(self, count: int): 
        self.positions_evaluated = count
    
    def reset_state(self):
        self.positions_evaluated = 0

    def get_positions_evaluated(self): 
        return self.positions_evaluated

    def get_match_stats(self) -> dict[str, object]:
        return {
            "heuristic_name": self.heuristic_name,
            "search_depth": self.search_depth,
            "positions_evaluated": self.positions_evaluated,
        }

    def configure(self, heuristic: HeuristicT, heuristic_name: str, search_depth: int, alfa_beta: bool = False) -> None:
        self.heuristic = heuristic
        self.heuristic_name = heuristic_name
        self.search_depth = search_depth
        self.alfa_beta = alfa_beta

    def set_heuristic(self, heuristic, name: str='base')-> None:
        self.heuristic = heuristic
        self.heuristic_name = name

    def set_search_depth(self, depth: int)-> None:
        self.search_depth = depth

    def set_alfa_beta(self, state: bool)-> None: 
        self.alfa_beta = state

    def handle_move(self, state: list[list[str]]) -> tuple[int, int, int, int, str]:
        best_score, best_move = self.minimax(state, self.search_depth, True, float('-inf'), float('inf'))

        (sy, sx), (ey, ex) = best_move
        return sx, sy, ex, ey, self.side

    def minimax(self, state: list[list[str]], depth: int, is_maximizing: bool, alpha: float, beta: float) -> tuple[float, tuple | None]:
        self.positions_evaluated += 1
        side_to_move = self.side if is_maximizing else self.opponent
        side_dir = self.direction if self.side == side_to_move else -1*self.direction
        is_over, terminal_score = self.is_terminal_state(state)
        if is_over: 
            return terminal_score, None

        if depth == 0:
            return self.heuristic(state, self.side, self.opponent, side_dir), None
        
        legal_moves = self.generate_legal_moves(state, side_to_move)
        

        if not legal_moves:
            if is_maximizing:
                return float('-inf'), None
            else:
                return float('inf'), None
            
        best_move = None

        if is_maximizing:
            max_eval = float('-inf')
            for move in legal_moves:

                new_state = [row[:] for row in state]
                
                self.apply_pseudo_move(new_state, move, side_to_move)                
                eval_score, _ = self.minimax(new_state, depth - 1, False, alpha, beta)
                
                if best_move is None or eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                    
                if self.alfa_beta:    
                    alpha = max(alpha, eval_score)
                    if beta <= alpha: 
                        break 
                
            return max_eval, best_move

        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_state = [row[:] for row in state]
                self.apply_pseudo_move(new_state, move, side_to_move)
                eval_score, _ = self.minimax(new_state, depth - 1, True, alpha, beta)
                
                if best_move is None or eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                    
                if self.alfa_beta:    
                    beta = min(beta, eval_score)
                    if beta <= alpha: 
                        break 
                
            return min_eval, best_move
        

    def generate_legal_moves(self, state: list[list[str]], side_to_move: str) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        moves = []
        direction = self.direction if side_to_move == self.side else -self.direction
        enemy = self.opponent if side_to_move == self.side else self.side

        for y in range(self.y):
            for x in range(self.x):
                if state[y][x] == side_to_move:
                    ny = y + direction
                    
                    if 0 <= ny < self.y:
                        
                        if state[ny][x] != side_to_move and state[ny][x] != enemy:
                            moves.append(((y, x), (ny, x)))
                        
                        for dx in [-1, 1]:
                            nx = x + dx
                            if 0 <= nx < self.x:
                                if state[ny][nx] != side_to_move:
                                    moves.append(((y, x), (ny, nx)))
                                    
        return moves

    def apply_pseudo_move(self, state: list[list[str]], move: tuple[tuple[int, int], tuple[int, int]], side: str):
        (sy, sx), (ey, ex) = move
        state[ey][ex] = state[sy][sx]
        state[sy][sx] = '_'

    def is_terminal_state(self, state: list[list[str]])-> tuple[bool, float]:
        last_row = state[self.y -1]
        first_row = state[0]
        if self.direction == 1: 
            if self.side in last_row: 
                return True, float('inf')
            if self.opponent in first_row: 
                return True, float('-inf')
            return False, 0.0 
        elif self.direction == -1:
            if self.side in first_row: 
                return True, float('inf')
            if self.opponent in last_row: 
                return True, float('-inf') 
            return False, 0.0 
        else: 
            raise Exception("No direction set for player")



class HPlayer(BasePlayer): 
    def __init__(self):
        super().__init__()
    
    def handle_move(self, state: list[list[str]]) -> tuple[int, int, int, int, str]:
        self.print_state(state)
        print(f"Grasz: {self.side}")
        
        while True:
            try:
                start_input = input("Podaj kolumnę (x) i wiersz (y) pionka (np. '1 6'): ")
                sx, sy = map(int, start_input.split())
                
                end_input = input("Podaj kolumnę (x) i wiersz (y) docelowe (np. '1 5'): ")
                ex, ey = map(int, end_input.split())
                
                return sx, sy, ex, ey, self.side
                
            except ValueError:
                print("Błędny format wejścia! Wpisz dokładnie dwie liczby całkowite oddzielone spacją.")

class RPlayer(CPlayer): 
    def handle_move(self, state: list[list[str]]) -> tuple[int, int, int, int, str]:
        moves = self.generate_legal_moves(state=state, side_to_move = self.side)
        best_move = random.choice(moves)
        (sy, sx), (ey, ex) = best_move
        return sx, sy, ex, ey, self.side