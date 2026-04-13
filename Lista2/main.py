from player import HPlayer, CPlayer, RPlayer
from game import Game, MatchResultsCsvWriter
from heuristic import sprinter_heuristic, material_heuristic, random_heuristic, phalanx_heuristic, passed_pawn_heuristic, center_control_heuristic

def run_match_series(player1: CPlayer, player2: CPlayer, games_count: int, output_name: str, board_x: int, board_y: int, update: bool):
    logger = MatchResultsCsvWriter(output_name, append=False)
    game = Game(board_x, board_y, player1=player1, player2=player2, starting_player='W', results_logger=logger)
    game.play_match_series(games_count=games_count, swap_player_order_each_game=True, summary=True, csv_data=True)


def test_all_players_base(players: list[CPlayer]):
        """Test all players against each other with base configuration"""
        for i, p1 in enumerate(players):
            for p2 in players[i+1:]:
                for depth in range(2, 6):
                    p1.set_search_depth(depth=depth)
                    p2.set_search_depth(depth=depth)
                    run_match_series(p1, p2, 2, "base_heur.csv", 8, 8, True)


def test_different_board_sizes(players):
    """Test with different board sizes at depth 4"""
    for size in [4, 6, 8, 10, 12]:
        players[1].configure(sprinter_heuristic, 'sprinter', 4, True)
        players[2].configure(material_heuristic, 'material', 4, True)
        run_match_series(players[1], players[2], 1, f"board_{size}x{size}.csv", size, size, True)

def test_alpha_beta_pruning(players):
    """Test with alpha-beta pruning on and off at depth 5"""
    players[1].configure(sprinter_heuristic, 'sprinter', 5, True)
    players[2].configure(material_heuristic, 'material', 5, False)
    run_match_series(players[1], players[2], 1, "pruning_on.csv", 8, 8, True)
    
    players[1].configure(sprinter_heuristic, 'sprinter', 5, False)
    players[2].configure(material_heuristic, 'material', 5, False)
    run_match_series(players[1], players[2], 1, "pruning_off.csv", 8, 8, True)



if __name__ == "__main__":
    random_player = RPlayer()
    sprinter_player = CPlayer()
    material_player = CPlayer()
    central_player = CPlayer()
    phalanx_player = CPlayer()
    passed_pawn_player = CPlayer()

    global_search_depth = 3

    random_player.search_depth=1
    random_player.heuristic_name='random'

    sprinter_player.configure(sprinter_heuristic, 'sprinter', global_search_depth, True)
    material_player.configure(material_heuristic, 'material', global_search_depth, True)
    central_player.configure(center_control_heuristic, 'center_control', global_search_depth, True)
    phalanx_player.configure(phalanx_heuristic, 'phalanx', global_search_depth, True)
    passed_pawn_player.configure(passed_pawn_heuristic, 'passed_pawn', global_search_depth, True)

    players = [random_player, sprinter_player, material_player, central_player, phalanx_player, passed_pawn_player]

    run_match_series(random_player, sprinter_player, 2, 'testing.csv', 8, 8, False)
    

    # test_all_players_base(players)
    # test_different_board_sizes(players)
    # test_alpha_beta_pruning(players)
