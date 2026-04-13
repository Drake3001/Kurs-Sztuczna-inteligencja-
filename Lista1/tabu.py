class TabuSearchRouter:

    def __init__(self, start_id, L_str, criteria, start_time, start_date, graph, dfs, g_func, h_func):

        self.start_id = start_id

        if isinstance(L_str, str):

            self.L_ids = [x.strip() for x in L_str.split(";") if x.strip()]

        else:

            self.L_ids = list(L_str)

        self.criteria = criteria

        self.start_time_sec = _time_to_seconds(start_time)

        self.start_date = start_date

        self.graph = graph

        self.dfs = dfs

        self.g_func = g_func

        self.h_func = h_func

        

        self.cache = {} 

        self.cache_hits = 0

        self.cache_misses = 0

        

    def _get_absolute_departure(self, start_time, path):

        walk_time = 0

        for e in path:

            if getattr(e, 'is_transfer', False) or getattr(e.edge_used, 'is_transfer', False):

                walk_time += e.edge_used.transfer_time

            else:

                gtfs_dep = e.edge_used.departure_time

                arrival_at_station = start_time + walk_time

                for day_offset in [-1, 0, 1, 2, 3]:

                    abs_dep = gtfs_dep + day_offset * 86400

                    if abs_dep >= arrival_at_station:

                        return abs_dep

                return gtfs_dep

        return None

        

    def _get_cached_path(self, origin, destination, current_time):

        entries = self.cache.get((origin, destination), [])

        for entry in entries:

            if entry.is_valid_for(current_time):

                self.cache_hits += 1

                return entry.path, entry.get_cost(current_time)

        self.cache_misses += 1

        return None, None

        

    def _cache_path(self, origin, destination, start_time, path, cost_or_inf):

        key = (origin, destination)

        if key not in self.cache:

            self.cache[key] = []

            

        departure_time = None

        if path:

            departure_time = self._get_absolute_departure(start_time, path)

            

        # Zwiększanie zakresu start_time, jeśli to samo połączenie

        if path and departure_time is not None:

            for entry in self.cache[key]:

                if entry.departure_time == departure_time:

                    # Rozszerzamy zakres, z którego to samo połączenie jest łapane

                    if start_time < entry.start_time:

                        entry.start_time = start_time

                    return # Zaktualizowano istniejący wpis

                    

        new_entry = PathCacheEntry(start_time, departure_time, path, cost_or_inf)

        self.cache[key].append(new_entry)



    def evaluate_permutation(self, perm):

        full_route = [self.start_id] + list(perm) + [self.start_id]

        

        current_time = self.start_time_sec

        current_date_str = self.start_date

        current_date_dt = datetime.strptime(self.start_date, "%Y%m%d")

        

        total_path = []

        

        for i in range(len(full_route) - 1):

            origin = full_route[i]

            destination = full_route[i+1]

            

            leg_path, cost_or_inf = self._get_cached_path(origin, destination, current_time)

            if leg_path is None:

                leg_path, cost_or_inf = find_path(origin, destination, current_time, current_date_str, self.graph, self.g_func, self.h_func)

                self._cache_path(origin, destination, current_time, leg_path, cost_or_inf)

                

            if not leg_path or len(leg_path) == 0:

                return float('inf'), []

                

            total_path.extend(leg_path)

            

            LARGE_VAL = 10**10

            arrival_time = cost_or_inf % LARGE_VAL if self.criteria == 'p' else cost_or_inf

                

            days_passed = arrival_time // 86400

            current_time = arrival_time

            

            if days_passed > 0:

                new_dt = current_date_dt + timedelta(days=days_passed)

                current_date_str = new_dt.strftime("%Y%m%d")

                

        total_transfers = 0

        prev_train_route = None

        

        for entry in total_path:

            if getattr(entry, 'is_transfer', False) or getattr(entry.edge_used, 'is_transfer', False):

                continue

                

            current_route = getattr(entry.edge_used, 'route_name', 'UNKNOWN')

            if prev_train_route is not None and current_route != prev_train_route:

                total_transfers += 1

            prev_train_route = current_route



        if self.criteria == 't':

            total_cost = current_time - self.start_time_sec

        else:

            LARGE_VAL = 10**10

            total_cost = (total_transfers * LARGE_VAL) + (current_time - self.start_time_sec) 

            

        return total_cost, total_path



    def solve(self, max_iter=8, max_no_improve=3, max_sampled_neighbors=4):

        t0 = time.perf_counter()

        

        current_solution = list(self.L_ids)

        best_cost, best_full_path = self.evaluate_permutation(current_solution)

        best_solution = list(current_solution)

        

        tabu_tenure = max(5, int(1.5 * len(self.L_ids)))

        tabu_list = deque()

        tabu_set = set()

        

        def add_to_tabu(sol):

            tup = tuple(sol)

            if len(tabu_list) >= tabu_tenure:

                oldest = tabu_list.popleft() 

                tabu_set.discard(oldest)    

            tabu_list.append(tup)

            tabu_set.add(tup)



        add_to_tabu(current_solution)

        

        iterations_without_improvement = 0

        

        for iteration in range(max_iter):

            neighborhood = []

            for i in range(len(current_solution)):

                for j in range(i + 1, len(current_solution)):

                    neighbor = list(current_solution)

                    neighbor[i], neighbor[j] = neighbor[j], neighbor[i]

                    neighborhood.append(neighbor)

                    

            if len(neighborhood) > max_sampled_neighbors:

                neighborhood = random.sample(neighborhood, max_sampled_neighbors)

                

            best_neighbor = None

            best_neighbor_cost = float('inf')

            best_neighbor_path = []

            

            for neighbor in neighborhood:

                cost, path = self.evaluate_permutation(neighbor)

                is_tabu = tuple(neighbor) in tabu_set

                

                if is_tabu and cost < best_cost:

                    is_tabu = False # Aspiration

                

                if not is_tabu and cost < best_neighbor_cost:

                    best_neighbor_cost = cost

                    best_neighbor = neighbor

                    best_neighbor_path = path



            if best_neighbor is None:

                break

                

            current_solution = best_neighbor

            add_to_tabu(current_solution)

            

            if best_neighbor_cost < best_cost:

                best_cost = best_neighbor_cost

                best_solution = list(best_neighbor)

                best_full_path = best_neighbor_path

                iterations_without_improvement = 0

            else:

                iterations_without_improvement += 1

                

            if iterations_without_improvement >= max_no_improve:

                break

                

        t1 = time.perf_counter()

        duration = t1 - t0

        

        return best_solution, best_cost, best_full_path, duration



    def print_solution(self, total_path, duration, total_cost):

        if not total_path:

            print(f"-1\n{duration:.4f}\n")

            print("Brak ścieżki spełniającej warunki.")

            return

            

        stops_df = self.dfs["stops.csv"]

        

        for entry in total_path:

            is_transfer = getattr(entry, 'is_transfer', False) or getattr(entry.edge_used, 'is_transfer', False)

            if is_transfer:

                continue

                

            origin_id = entry.orgin_node_id 

            target_id = entry.edge_used.target_stop_id

            

            origin_name = get_stop_name(stops_df, origin_id)

            target_name = get_stop_name(stops_df, target_id)

            

            route_name = getattr(entry.edge_used, 'route_name', 'UNKNOWN')

            dep_time = format_time(entry.edge_used.departure_time)

            arr_time = format_time(entry.edge_used.arrival_time)

            

            print(f"{origin_name} -> {target_name} | linia: {route_name} | {dep_time} - {arr_time}")



        print()    

            

        print(f"Koszt (min_kryterium): {total_cost}")

        print(f"Czas obliczen [s]: {duration:.4f}")

        print(f"Cache Statystyki: Hits={self.cache_hits}, Misses={self.cache_misses}")