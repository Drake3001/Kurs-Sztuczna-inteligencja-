from dataclasses import dataclass


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
    departure_time: int
    arrival_time: int 
    route_name: str 
    service_id: str
    date_start: str = ""  
    date_end: str = ""   
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
        self.regular_schedules = {}
        self.exceptions = {}
    def set_schedules(self, schedules: dict): 
        self.regular_schedules = schedules
    def set_exceptions(self, exceptions: dict): 
        self.exceptions = exceptions

    def is_active(self, service_id: str, date_str: str) -> bool:
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
        weekday = date(year, month, day).weekday()        
        return schedule['days'][weekday] == 1


def add_days_to_date(date_str: str, days: int) -> str:
    # date_str to "YYYYMMDD" helper dla TransitGraph 
    dt = datetime.strptime(date_str, "%Y%m%d")
    dt += timedelta(days=days)
    return dt.strftime("%Y%m%d")


class TransitGraph():
    def __init__(self):
        self.nodes : dict[str ,Node] = {}
        self.adjacent : dict[str, list[BaseEdge]] = {} 
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

    def get_valid_neighbours(self, source_node_id: str, current_time: int, start_date: str) -> list:
        valid_moves = []
        neighbours = self.adjacent.get(source_node_id, [])


        soonest_regular_edges = {}

        for edge in neighbours:
            if isinstance(edge, TransferEdge):
                arrival_time = current_time + edge.transfer_time
                valid_moves.append((edge, arrival_time))
            
            else:
                current_day_offset = current_time // 86400
                for day_offset in [current_day_offset - 1, current_day_offset, current_day_offset + 1]:
                    check_date = add_days_to_date(start_date, day_offset)
                    
                    shifted_departure = edge.departure_time + (day_offset * 86400)
                    shifted_arrival = edge.arrival_time + (day_offset * 86400)
                    
                    if shifted_departure >= current_time:
                        # Czy ten pociąg kursuje w dniu check_date?
                        if self.calendar.is_active(edge.service_id, check_date):
                            key = (edge.target_stop_id, edge.route_name)
                            
                            if key not in soonest_regular_edges or shifted_departure < soonest_regular_edges[key][1]: 
                                soonest_regular_edges[key] = (edge, shifted_departure, shifted_arrival)



        for edge, shifted_dep, shifted_arr in soonest_regular_edges.values():
            valid_moves.append((edge, shifted_arr))

        valid_moves.sort(key=lambda x: x[1])
        return valid_moves
    
    def check_content(self): 
        print("Nodes count", len(self.nodes.keys()))
        print("Edges count", sum([len(x) for x in self.adjacent.values()]))
