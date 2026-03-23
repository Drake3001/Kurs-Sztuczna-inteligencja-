import pandas as pd
from models import Node, TransferEdge, RegularEdge, TransitGraph, TransitCalendar

def time_to_seconds(time_str: str) -> int:
    if pd.isna(time_str) or time_str == "":
        return 0
    try:
        parts = str(time_str).split(':')
        if len(parts) != 3:
            print(f"Warning: Invalid time format '{time_str}', using 0")
            return 0
        h, m, s = map(int, parts)
        if not (0 <= h <= 48 and 0 <= m <= 59 and 0 <= s <= 59):
            print(f"Warning: Invalid time values in '{time_str}', using 0")
            return 0
        return h * 3600 + m * 60 + s
    except (ValueError, AttributeError) as e:
        print(f"Warning: Error parsing time '{time_str}': {e}, using 0")
        return 0

def load_stops(df: pd.DataFrame):
    res = []
    grouped = {}
    
    for row in df.itertuples():
        # 1. Pobieramy ID i usuwamy potencjalne .0 na końcu
        current_stop_id = str(row.stop_id)
        if current_stop_id.endswith('.0'):
            current_stop_id = current_stop_id[:-2]
            
        # 2. To samo dla parent_station
        parent_station_id = ""
        if pd.notna(row.parent_station):
            parent_station_id = str(row.parent_station)
            if parent_station_id.endswith('.0'):
                parent_station_id = parent_station_id[:-2]

        node = Node(
            stop_id = current_stop_id, 
            stop_name = str(row.stop_name), 
            stop_lat = float(row.stop_lat), 
            stop_lon = float(row.stop_lon), 
            type = int(row.location_type) if pd.notna(row.location_type) else 0, 
            parent_station = parent_station_id,  
        )
        res.append(node)
        
        # 3. Teraz klucze w słowniku wreszcie się pokryją!
        group_key = parent_station_id if parent_station_id != "" else current_stop_id
        
        cr_list = grouped.get(group_key, [])
        cr_list.append(node)
        grouped[group_key] = cr_list
        
    print(f"Created {len(res)} nodes")
    return (res, grouped)

def create_transfer_edges(grouped: dict[str, list], const_transfer_time: int ):
    transfer_edges = {}
    transfer_count = 0
    for parent_id, nodes in grouped.items():
        if len(nodes) < 2:
            continue
            
        for source_node in nodes:
            cr_transfer =[]
            for target_node in nodes:
                if source_node.stop_id != target_node.stop_id:
                    transfer_time_sec =const_transfer_time
                    transfer_edge = TransferEdge(
                        target_stop_id=target_node.stop_id,
                        transfer_time=transfer_time_sec,
                        is_transfer=True
                    )
                    
                    cr_transfer.append(transfer_edge)
            transfer_edges[source_node.stop_id] = cr_transfer
            transfer_count+=len(cr_transfer)
                    
    print(f"Created {transfer_count} transfer edges")
    return transfer_edges

def load_edges(df_routes: pd.DataFrame, df_trips: pd.DataFrame, df_stop_times: pd.DataFrame, graph: TransitGraph):
    routes = {}
    trips = {}
    count = 1
    
    for row in df_routes.itertuples():
        if pd.isna(row.route_short_name) or str(row.route_short_name).strip() == "":
            routes[row.route_id] = str(row.route_long_name)
        else:
            routes[row.route_id] = str(row.route_short_name)
            
    for row in df_trips.itertuples(): 
        trips[row.trip_id] = {
            "route_id": row.route_id, 
            "service_id": row.service_id
        }
        
    df_stop_times = df_stop_times.sort_values(["trip_id", "stop_sequence"])
    
    prev = None 
    for row in df_stop_times.itertuples():
        if prev and prev.trip_id == row.trip_id:
            trip_info = trips[row.trip_id]
            route_name = routes[trip_info["route_id"]]
            
            edge = RegularEdge(
                target_stop_id=str(row.stop_id),
                departure_time=time_to_seconds(prev.departure_time), 
                arrival_time=time_to_seconds(row.arrival_time),     
                route_name=route_name,
                service_id=str(trip_info["service_id"]),
                is_transfer=False
            )
            
            graph.add_edge(str(prev.stop_id), edge)
            count+=1

        prev = row
    print(f"Created {count} edges")

def load_calendar(df_calendar: pd.DataFrame):
    regular_schedules = {}
    for row in df_calendar.itertuples():
        regular_schedules[str(row.service_id)] = {
            'start': str(row.start_date),
            'end': str(row.end_date),
            'days': [
                row.monday, row.tuesday, row.wednesday, 
                row.thursday, row.friday, row.saturday, row.sunday
            ]
        }
    print(f"Created {len(regular_schedules)} schedules")
    return regular_schedules

def load_calendar_dates(df_calendar_dates: pd.DataFrame):
    exceptions = {}
    for row in df_calendar_dates.itertuples():
        sid = str(row.service_id)
        date_str = str(row.date)
        ex_type = int(row.exception_type)
        
        if sid not in exceptions:
            exceptions[sid] = {'added': set(), 'removed': set()}
            
        if ex_type == 1:
            exceptions[sid]['added'].add(date_str)
        elif ex_type == 2:
            exceptions[sid]['removed'].add(date_str)
    print(f"Created {len(exceptions)} exceptions")
    return exceptions 
