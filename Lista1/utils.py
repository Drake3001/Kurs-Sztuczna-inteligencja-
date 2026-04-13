from models import RouteObject, TransferEdge
import pandas as pd

def reconstruct_path(came_from: dict, current_state: tuple): 
    path = []
    
    while current_state in came_from:
        entry = came_from[current_state]
        
        prev_state = entry['prev_state']
        edge = entry['edge_used']
        
        is_transfer = isinstance(edge, TransferEdge)
        
        prev_node_id = prev_state[0]
        
        routeob = RouteObject(
            orgin_node_id=prev_node_id, 
            edge_used=edge, 
            is_transfer=is_transfer
        )
        
        path.append(routeob)
        
        current_state = prev_state
        
    path.reverse()
    return path

def format_time(seconds: int) -> str:
    """Zamienia sekundy od północy na format HH:MM:SS"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h >= 24:
        h -= 24
    return f"{h:02d}:{m:02d}:{s:02d}"

def get_stop_name(stops_df: pd.DataFrame, stop_id: str) -> str:
    """Bezpiecznie wyciąga nazwę przystanku na podstawie jego ID z DataFrame'a"""
    matching_stops = stops_df[stops_df['stop_id'].astype(str) == str(stop_id)]
    
    if not matching_stops.empty:
        return str(matching_stops['stop_name'].values[0])
    return f"Nieznany Przystanek (ID: {stop_id})"


def _time_to_seconds(time_str) -> int:
    if isinstance(time_str, int):
        return time_str
    parts = str(time_str).split(':')
    if len(parts) == 3:
        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    return 0