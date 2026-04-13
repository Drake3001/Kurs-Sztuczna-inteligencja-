from __future__ import annotations
from player import BasePlayer, CPlayer, HPlayer
from logger import MatchResultsCsvWriter
from datetime import datetime
import time 


class Game: 
    def __init__(self, x_size: int , y_size: int, player1: BasePlayer, player2: BasePlayer, symbol1: str = 'W', symbol2: str = 'B', starting_player: str = 'W', results_logger: MatchResultsCsvWriter | None = None):
        self.p1: BasePlayer= player1
        self.p2: BasePlayer= player2
        self.x: int= x_size
        self.y: int= y_size
        self.symbol1: str = symbol1
        self.symbol2: str  = symbol2
        self.move_count: int = 0 
        self.board: list[list[chr]] = []
        self.finished: bool = False 
        self.results_logger = results_logger
        if starting_player not in [self.symbol1, self.symbol2]: 
            raise Exception("Starting player must either match symbol1 or symbol2")
        self.start_time: float = 0.0
        self.end_time : float = 0.0 
        self.starting_player = starting_player
        self.prepare_next_match()


    def reset_game(self, change_player_side: bool = False, resize_board: tuple[bool, int, int] = (False, 0, 0)):
        resize = None
        if resize_board[0]:
            resize = (resize_board[1], resize_board[2])
        self.prepare_next_match(swap_player_order=change_player_side, resize_board=resize)

    def prepare_next_match(self, swap_player_order: bool = False, resize_board: tuple[int, int] | None = None):
        if swap_player_order:
            self._swap_starting_player()
        if resize_board is not None:
            self.x = resize_board[0]
            self.y = resize_board[1]

        self._reset_runtime_state()
        self.init_board()
        self.set_player_sides()
        self.set_players()
        self._reset_players_runtime_state()

    def play_match_series(self, games_count: int, swap_player_order_each_game: bool = True, summary: bool = False, csv_data: bool = False) -> list[str]:
        if games_count <= 0:
            raise Exception("games_count should be greater than 0")

        winners: list[str] = []
        for game_idx in range(games_count):
            if game_idx > 0:
                self.prepare_next_match(swap_player_order=swap_player_order_each_game)
            winners.append(self.play_game(summary=summary, csv_data=csv_data))
        return winners

    def _reset_runtime_state(self):
        self.finished = False
        self.move_count = 0
        self.start_time = 0.0
        self.end_time = 0.0

    def _reset_players_runtime_state(self):
        self.p1.reset_state()
        self.p2.reset_state()

    def _swap_starting_player(self):
        self.starting_player = self.symbol2 if self.starting_player == self.symbol1 else self.symbol1


    def init_board(self):
        if self.x < 0 or self.y<4:
            raise Exception("x_size should be greater than 0, y_size should be greater or equal to 4")
        self.board = []
        for _ in range(2):
            tmp = [self.symbol1 for _ in range(self.x)]
            self.board.append(tmp) 

        for i in range(self.y-4):
             tmp = ['_' for i in range(self.x)]
             self.board.append(tmp)

        for _ in range(2):
            tmp = [self.symbol2 for _ in range(self.x)]
            self.board.append(tmp)
            
    def set_player_sides(self):
        if self.starting_player == self.symbol1:
            self.p1.set_side(self.symbol1)
            self.p2.set_side(self.symbol2)
        else:
            self.p1.set_side(self.symbol2)
            self.p2.set_side(self.symbol1)

    def set_players(self): 
        self.p1.set_x_size(self.x)
        self.p1.set_y_size(self.y)
        self.p1.set_opponent(self.symbol2 if self.p1.get_side() == self.symbol1 else self.symbol1)
        self.p1.set_direction(1 if self.p1.get_side() == self.symbol1 else -1)
        self.p2.set_x_size(self.x)
        self.p2.set_y_size(self.y)
        self.p2.set_opponent(self.symbol1 if self.p2.get_side() == self.symbol2 else self.symbol2)
        self.p2.set_direction(1 if self.p2.get_side() == self.symbol1 else -1)


    def configure_results_logger(self, results_logger: MatchResultsCsvWriter):
        self.results_logger = results_logger

    def check_move_legality(self, start_pos: tuple[int, int], end_pos: tuple[int, int], player_side: str) -> tuple[bool, str]:
        st_y, st_x = start_pos
        ed_y, ed_x = end_pos

        if not (0 <= st_x < self.x and 0 <= ed_x < self.x and 0 <= st_y < self.y and 0 <= ed_y < self.y):
            return False, "Współrzędne znajdują się poza planszą."

        if self.board[st_y][st_x] != player_side:
            return False, "Na wybranym polu startowym nie ma Twojego pionka."

        forward_step = 1 if player_side == self.symbol1 else -1

        dy = ed_y - st_y
        dx = ed_x - st_x

        if dy != forward_step:
            return False, "Pionki mogą poruszać się wyłącznie o jedno pole do przodu."

        if abs(dx) > 1:
            return False, "Pionek może poruszać się tylko prosto lub po skosie o jedno pole."

        target_cell = self.board[ed_y][ed_x]

        if dx == 0:
            if target_cell in [self.symbol1, self.symbol2]:
                return False, "Pole na wprost jest zajęte. Bicie możliwe jest tylko po skosie."
        
        else:
            if target_cell == player_side:
                return False, "Pole po skosie jest zajęte przez Twój własny pionek."
        return True, "Ruch dozwolony."
    
    def make_move(self, start_pos: tuple[int, int], end_pos: tuple[int, int])-> bool:
        symbol = self.board[start_pos[0]][start_pos[1]]
        self.board[start_pos[0]][start_pos[1]] = '_'
        self.board[end_pos[0]][end_pos[1]] = symbol
        
        # Check standard win condition (reaching the end)
        if (symbol == self.symbol1 and end_pos[0] == self.y - 1) or (symbol == self.symbol2 and end_pos[0] == 0):
            return True
            
        # Check if the opponent ran out of pawns
        opponent_symbol = self.symbol2 if symbol == self.symbol1 else self.symbol1
        opponent_has_pawns = any(opponent_symbol in row for row in self.board)
        
        return not opponent_has_pawns
    
    def play_game(self, summary: bool = False, csv_data: bool = False)-> str:
        curr_player  = self.p2 if self.symbol1 == self.starting_player else self.p1 
        other_player = self.p2 if curr_player == self.p1 else self.p1
        self.start_time = time.perf_counter()
        while not self.finished:
            curr_player, other_player = other_player, curr_player
            sx, sy, ex, ey, side =curr_player.handle_move(self.board)
            legal, reason = self.check_move_legality((sy, sx), (ey, ex), side)
            if not legal:  
                sx, sy, ex, ey, side= self.handle_incorrect_move(player=curr_player, reason=reason)
            self.finished = self.make_move((sy, sx),(ey, ex))
            self.move_count +=1
        self.end_time = time.perf_counter() 
        winner = curr_player
        if summary: 
            self.print_game_summary(winner)
        if self.results_logger is not None:
            self.results_logger.log_match_result(self._build_match_record(winner))
        elif csv_data:
            raise Exception("CSV logging requested but no results logger was configured.")
        return winner.get_side()

    def _build_match_record(self, winner: BasePlayer) -> dict[str, object]:
        p1_stats = self.p1.get_match_stats()
        p2_stats = self.p2.get_match_stats()
        winnerdata = winner.get_match_stats()
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "winner": winner.get_side(),
            "winner_heuristic": winnerdata.get("heuristic_name", ""),
            "move_count": self.move_count,
            "board_width": self.x,
            "board_height": self.y,
            "starting_player": self.starting_player,
            "player1_class": self.p1.__class__.__name__,
            "player1_side": self.p1.get_side(),
            "player1_heuristic": p1_stats.get("heuristic_name", ""),
            "player1_search_depth": p1_stats.get("search_depth", ""),
            "player2_class": self.p2.__class__.__name__,
            "player2_side": self.p2.get_side(),
            "player2_heuristic": p2_stats.get("heuristic_name", ""),
            "player2_search_depth": p2_stats.get("search_depth", ""),
            "player2_positions_evaluated": p2_stats.get("positions_evaluated", ""),
            "player1_positions_evaluated": p1_stats.get("positions_evaluated", ""), 
            "time_played": (str(self.end_time - self.start_time)+'s')
        }
        return self.results_logger.build_record(record) if self.results_logger is not None else record

    def print_game_summary(self, player: BasePlayer):
        print(30*"=")
        self.print_state()
        print(f"Zwycięzca: {player.get_side()}")
        print(f"Wygrana w {self.move_count} ruchach")
        print(f"Rozmiar planszy: {self.x}x{self.y}")
        print(30*"=")

    def print_state(self):
        print(f"\n--- Ustawienie ---")
        for i, row in enumerate(self.board): 
            print(f"{i} | " + " ".join(row))
        
        print("-" * (self.x * 2 + 4))
        print("    " + " ".join(str(i) for i in range(self.x)))
        print()

    def handle_incorrect_move(self, player: BasePlayer, reason: str)-> tuple[int, int, int, int, str]:
        if isinstance(player, HPlayer):
            legal =False
            while not legal: 
                print(reason)
                sx, sy, ex, ey, side =player.handle_move(self.board)
                legal, reason = self.check_move_legality((sy, sx), (ey, ex), side)
            return sx, sy, ex, ey, side
        elif isinstance(player, CPlayer): 
            raise Exception("CPlayer can't call illegal moves")
        else: 
            raise Exception("Player must be either of HPlayer or CPlayer class")
