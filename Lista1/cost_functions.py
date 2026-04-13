import math

def calc_distance(st_lat, st_lon, ed_lat, ed_lon):
    R = 6371000.0 
    
    lat1 = math.radians(st_lat)
    lon1 = math.radians(st_lon)
    lat2 = math.radians(ed_lat)
    lon2 = math.radians(ed_lon)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance

#funckje kosztu dla kryterium t
def g_cost_time(current_g, is_transfer, arrival_time, is_start):
    return arrival_time

def h_cost_time(node, target_node):
    dist = calc_distance(node.stop_lat, node.stop_lon, target_node.stop_lat, target_node.stop_lon)
    v_ms = 44.0 
    return dist / v_ms

def g_cost_transfers(current_g, is_transfer, arrival_time, is_start):
    LARGE = 10**10
    if is_start:
        return arrival_time
    base_transfers = current_g // LARGE
    if is_transfer:
        base_transfers += 1
    return base_transfers * LARGE + arrival_time

def h_cost_transfers(node, target_node):
    return 0
