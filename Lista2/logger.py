from __future__ import annotations
import csv
import os
from datetime import datetime

class MatchResultsCsvWriter:
    DEFAULT_FIELDNAMES = [
        "timestamp",
        "winner",
        "winner_heuristic",
        "move_count",
        "board_width",
        "board_height",
        "starting_player",
        "player1_class",
        "player1_side",
        "player1_heuristic",
        "player1_search_depth",
        "player1_positions_evaluated",
        "player2_class",
        "player2_side",
        "player2_heuristic",
        "player2_search_depth",
        "player2_positions_evaluated",
        "time_played", 
    ]

    def __init__(self, file_path: str, append: bool = True, fieldnames: list[str] | None = None):
        self.file_path = file_path
        self.append = append
        self.fieldnames = fieldnames or self.DEFAULT_FIELDNAMES
        self._initialize_file()

    def _initialize_file(self):
        if not self.append or not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            with open(self.file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()

    def log_match_result(self, record: dict[str, object]):
        mode = "a"
        needs_header = not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0
        with open(self.file_path, mode, newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            if needs_header:
                writer.writeheader()
            writer.writerow(record)

    def build_record(self, record: dict[str, object]) -> dict[str, object]:
        row = {key: record.get(key, "") for key in self.fieldnames}
        return row