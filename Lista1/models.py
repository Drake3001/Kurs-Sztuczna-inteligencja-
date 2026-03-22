from dataclasses import dataclass
import datetime

@dataclass 
class BaseEdge:
    target_stop_id: str
    is_transfer: bool

@dataclass
class TransferEdge(BaseEdge): 
    transfer_time: int = 60

@dataclass 
class RegularEdge(BaseEdge):
    target_stop_id: str
    departure_time: int # sekundy od północy
    arrival_time: int 
    route_name: str 
    service_id: str
    is_transfer = False

@dataclass
class Node: 
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float 
    type: int
    parent_station: str 

@dataclass
class RouteObject:
    orgin_node_id: str
    edge_used: BaseEdge
    is_transfer: bool

class TransitCalendar:
    def __init__(self):
        # service_id -> { 'start': 'YYYYMMDD', 'end': 'YYYYMMDD', 'days': [mon, tue, wed, thu, fri, sat, sun] }
        self.regular_schedules = {}
        # service_id -> { 'added': set(), 'removed': set() }
        self.exceptions = {}
    def set_schedules(self, schedules: dict): 
        self.regular_schedules = schedules
    def set_exceptions(self, exceptions: dict): 
        self.exceptions = exceptions

    def is_active(self, service_id: str, date_str: str) -> bool:
        """
        Sprawdza, czy pociąg faktycznie jedzie w podanym dniu.
        Format daty to YYYYMMDD, np. '20260308'.
        """
        if service_id in self.exceptions:
            if date_str in self.exceptions[service_id]['removed']:
                return False
            if date_str in self.exceptions[service_id]['added']:
                return True
                
        if service_id not in self.regular_schedules:
            return False
            
        schedule = self.regular_schedules[service_id]
        
        if not (schedule['start'] <= date_str <= schedule['end']):
            return False
            
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        weekday = datetime.date(year, month, day).weekday()        
        return schedule['days'][weekday] == 1

class TransitGraph():
    def __init__(self):
        self.nodes : dict[str ,Node] = {}
        self.adjacent : dict[str, list[BaseEdge]] = {} # klucz id wierzchołka, wartość lista krawędzie skierowanych od tego wierzchołka
        self.calendar: TransitCalendar = {}
    def add_nodes(self, nodes: list[Node]): 
        for entry in nodes: 
            self.nodes[entry.stop_id]=entry
    def add_edge(self, source_node_id: str,edge: BaseEdge):
        curr = self.adjacent.get(source_node_id, [])
        curr.append(edge)
        self.adjacent[source_node_id] = curr
    def add_edges(self, edge_dict: dict[str, BaseEdge]):
        for key, value in edge_dict.items():
            curr = self.adjacent.get(key, [])
            curr += value  
            self.adjacent[key] = curr 
    def set_calendar(self, calendar: TransitCalendar): 
        self.calendar= calendar
    def get_valid_neighbours(self, source_node_id: str, current_time: int, current_date: str) -> list:
        valid_moves = [] 
        neighbours = self.adjacent.get(source_node_id, []) 
        
        for edge in neighbours:
            if isinstance(edge, TransferEdge):
                continue
                
            if edge.departure_time >= current_time and self.calendar.is_active(edge.service_id, current_date):
                valid_moves.append((edge, edge.arrival_time, False))
                
        for transfer_edge in neighbours: 
            if not isinstance(transfer_edge, TransferEdge):
                continue
                
            time_after_transfer = current_time + transfer_edge.transfer_time
            target_platform = transfer_edge.target_stop_id
            
            next_neighbours = self.adjacent.get(target_platform, [])
            for next_edge in next_neighbours: 
                if isinstance(next_edge, TransferEdge):
                    continue
                    
                if next_edge.departure_time >= time_after_transfer and self.calendar.is_active(next_edge.service_id, current_date):
                    valid_moves.append((next_edge, next_edge.arrival_time, True))
                    
        return valid_moves
    
    def check_content(self): 
        print("Nodes count", len(self.nodes.keys()))
        print("Edges count", sum([len(x) for x in self.adjacent.values()]))
