import pandas as pd
from models import RouteObject

#odtworzenie ścieżki algorytmu 
def reconstruct_path(came_from: dict, current_id: str): 
    path = []
    while current_id in came_from:
        entry = came_from[current_id]
        routeob = RouteObject(entry['prev_node'], entry['edge_used'], entry['is_transfer'])
        path.append(routeob)
        current_id = routeob.orgin_node_id
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

def res_printing(path: list, stops_df: pd.DataFrame):
    if not path:
        print("Trasa jest pusta! Algorytm nie znalazł połączenia.")
        return

    print("=" * 60)
    print("SZCZEGÓŁY TWOJEJ PODRÓŻY")
    print("=" * 60)

    transfer_count = 0
    
    start_time = path[0].edge_used.departure_time
    end_time = path[-1].edge_used.arrival_time

    for i, entry in enumerate(path):
        origin_id = entry.orgin_node_id 
        target_id = entry.edge_used.target_stop_id
        
        origin_name = get_stop_name(stops_df, origin_id)
        target_name = get_stop_name(stops_df, target_id)
        
        dep_time = format_time(entry.edge_used.departure_time)
        arr_time = format_time(entry.edge_used.arrival_time)
        route = entry.edge_used.route_name
        
        if entry.is_transfer:
            transfer_count += 1
            print(f"[ZMIANA PERONU / PRZESIADKA na stacji {origin_name}]")
            
        print(f"{dep_time} | Odjazd:   {origin_name}")
        print(f"   |          (Linia: {route})")
        print(f"{arr_time} | Przyjazd: {target_name}")
        
        if i < len(path) - 1:
            print("-" * 40)


    total_time_minutes = (end_time - start_time) // 60

    print("=" * 60)
    print("PODSUMOWANIE")
    print("=" * 60)
    print(f"Trasa:             {get_stop_name(stops_df, path[0].orgin_node_id)} ➔ {get_stop_name(stops_df, path[-1].edge_used.target_stop_id)}")
    print(f"Godzina wyjazdu:   {format_time(start_time)}")
    print(f"Godzina przyjazdu: {format_time(end_time)}")
    print(f"Całkowity czas:    {total_time_minutes} minut")
    print(f"Liczba przesiadek: {transfer_count}")
    print("=" * 60)
