from player import CPlayer 
import random
from dataclasses import dataclass, field
from heuristic import HeuristicT, heuristic_factory, sprinter_heuristic, material_heuristic, phalanx_heuristic
from game import Game
from datetime import datetime
from logger import MatchResultsCsvWriter

@dataclass(order=True)
class Specimen:
    fitness: float
    weights: list[float] = field(compare=False)
    heuristic: HeuristicT = field(compare=False)
    epoch: int = field(default=0, compare=False)

class GeneticAlgorithm:
    def __init__(self, weights_count: int = 5, x_size: int = 8, y_size: int = 8, search_depth: int = 3):
        self.weights_ct = weights_count
        self.phases = 3
        self.base_players = [sprinter_heuristic, material_heuristic, phalanx_heuristic]
        self.output = f'{datetime.now()}_genetic.txt'
        self.player1 = CPlayer()
        self.player2 = CPlayer()
        self.player1.set_search_depth(search_depth)
        self.player2.set_search_depth(search_depth)
        self.player1.set_alfa_beta(True)
        self.player2.set_alfa_beta(True)
        self.game = Game(x_size=x_size, y_size=y_size, player1=self.player1, player2=self.player2, symbol1='W', symbol2='B')
        logger = MatchResultsCsvWriter('new_gen_alg.csv', append=True)
        self.game.configure_results_logger(logger)

    
    def initial_population(self, count: int):
        res = []
        for _ in range(count):
            temp = []
            for _ in range(self.phases): 
                raw_weights = [random.random() for i in range(self.weights_ct)]
                total_sum = sum(raw_weights)
                normalized_weights = [w / total_sum for w in raw_weights]
                temp+=normalized_weights
            res.append(temp)
        return res
    
    def run_two_games(self, weight: float, evaluated: HeuristicT, function2: HeuristicT)-> tuple[float, float]:
        self.game.prepare_next_match()
        values = 0.0
        secondary = 0.0 
        self.player1.set_heuristic(evaluated)
        self.player2.set_heuristic(function2)
        winner = self.game.play_game(summary=False)
        if winner == 'W':
            values+= weight
        else: 
            secondary+= weight
        self.game.prepare_next_match()
        self.player1.set_heuristic(function2)
        self.player2.set_heuristic(evaluated)
        winner = self.game.play_game(summary=False)
        if winner == 'B':
            values+= weight
        else: 
            secondary+= weight
        return values, secondary
        
    def run(
        self, epochs: int, population_size: int, current_duels: int, hall_duels: int,
        transfer_count: int, base_weight: float = 1.0, past_weight: float = 1.0,
        current_weight: float = 1.0, x_size: int = 8, y_size: int = 8, mutation_rate: float = 0.2, mutation_strength: float = 0.15) -> list['Specimen']:
        
        initial = self.initial_population(population_size)
        population = [Specimen(fitness=0.0, weights=entry, heuristic=heuristic_factory(entry)) for entry in initial]
        hall_of_fame = []
        
        for epoch in range(epochs):
            print(f"epoch-{epoch}")
            for specimen in population:
                specimen.fitness = 0.0
                for dueler in self.base_players:
                    evaluated, _ = self.run_two_games(base_weight, specimen.heuristic, dueler)
                    specimen.fitness += evaluated
                for _ in range(current_duels): 
                    rival = random.choice(population)
                    evaluated, _ = self.run_two_games(current_weight, specimen.heuristic, rival.heuristic)
                    specimen.fitness += evaluated
                if hall_of_fame and hall_duels > 0:
                    for _ in range(hall_duels): 
                        rival = random.choice(hall_of_fame)
                        evaluated, _ = self.run_two_games(past_weight, specimen.heuristic, rival.heuristic)
                        specimen.fitness += evaluated
            
            population.sort(reverse=True)
            best = population[0]
            hall_of_fame.append(Specimen(fitness=best.fitness, weights=best.weights, heuristic=best.heuristic, epoch=epoch))
            
            
            if epoch == 0:
                csv_filename = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_training_log.csv'
                with open(csv_filename, "w") as f:
                    headers = ["epoch", "fitness"] + [f"w{i+1}" for i in range(len(best.weights))]
                    f.write(",".join(headers) + "\n")
            
            weights_str = ",".join([f"{w:.4f}" for w in best.weights])
            champ_fitness = best.fitness
            with open(csv_filename, "a") as f:
                f.write(f"{epoch},{champ_fitness},{weights_str}\n")
            
            new_population_weights = []
            survivors = population[:transfer_count]
            for spec in survivors:
                new_population_weights.append(spec.weights)
                
            for i in range(population_size - transfer_count):
                w1 = random.choice(survivors).weights
                w2 = random.choice(survivors).weights
                child = self.crossover_and_mutate(w1, w2, mutation_rate=mutation_rate, mutation_strength=mutation_strength)
                new_population_weights.append(child)
            
            population = [Specimen(fitness=0.0, weights=entry, heuristic=heuristic_factory(entry)) for entry in new_population_weights]
            
        return hall_of_fame

            
    def crossover_and_mutate(self, parent1_weights: list[float], parent2_weights: list[float], 
                             mutation_rate: float = 0.2, mutation_strength: float = 0.15) -> list[float]:
        child_weights = []
        
        # Iterujemy po fazach gry (0, 1, 2)
        for phase in range(self.phases):
            # Wyliczamy indeksy dla danej fazy (np. 0-5, 5-10, 10-15)
            start_idx = phase * self.weights_ct
            end_idx = start_idx + self.weights_ct
            
            # Wycinamy geny tylko dla tej jednej fazy
            p1_chunk = parent1_weights[start_idx:end_idx]
            p2_chunk = parent2_weights[start_idx:end_idx]
            
            chunk_child = []
            
            # Krzyżujemy i mutujemy wewnątrz fazy
            for w1, w2 in zip(p1_chunk, p2_chunk):
                new_w = (w1 + w2) / 2.0 
                
                if random.random() < mutation_rate:
                    noise = random.uniform(-mutation_strength, mutation_strength)
                    new_w += noise
                    
                new_w = max(0.0, new_w)
                chunk_child.append(new_w)
                
            # NORMALIZACJA TYLKO DLA TEJ FAZY
            total_sum = sum(chunk_child)        
            if total_sum == 0:
                normalized_chunk = [1.0 / self.weights_ct] * self.weights_ct
            else:
                normalized_chunk = [w / total_sum for w in chunk_child]  
                
            # Doklejamy znormalizowaną fazę do pełnego genotypu dziecka
            child_weights.extend(normalized_chunk)
            
        return child_weights

    def final_showdown(self, hall_of_fame: list[Specimen], duels_search_depth: int):
        self.player1.set_search_depth(duels_search_depth) 
        self.player2.set_search_depth(duels_search_depth) 
        if not hall_of_fame:
            print("Hall of fame is empty. No showdown to run.")
            return
            
        scores = {i: 0.0 for i in range(len(hall_of_fame))}
        
        for i in range(len(hall_of_fame)):
            for j in range(i + 1, len(hall_of_fame)):
                score_i, score_j = self.run_two_games(1.0, hall_of_fame[i].heuristic, hall_of_fame[j].heuristic)
                scores[i] += score_i
                scores[j] += score_j

        results = sorted([(scores[i], hall_of_fame[i]) for i in range(len(hall_of_fame))], key=lambda x: x[0], reverse=True)
        
        safe_output_name = self.output.replace(':', '-')
        
        with open(safe_output_name, 'w') as f:
            f.write("=== FINAL SHOWDOWN RESULTS ===\n")
            f.write(f"Total contenders: {len(hall_of_fame)}\n")
            f.write("=" * 50 + "\n\n")
            
            for rank, (score, specimen) in enumerate(results, 1):
                f.write(f"Rank {rank}:\n")
                f.write(f"  Score  : {score:.2f} points\n")
                f.write(f"  Epoch  : {specimen.epoch}\n")
                formatted_weights = ", ".join([f"{w:.4f}" for w in specimen.weights])
                f.write(f"  Weights: [{formatted_weights}]\n")
                f.write("-" * 50 + "\n")
                
        print(f"Final showdown complete. Results saved to {safe_output_name}")


    def read_training_log(self, filename: str) -> list['Specimen']:
        """Read training log CSV and return list of champion specimens."""
        champions = []
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return champions
                
                # Parse header to get weight count
                header = lines[0].strip().split(',')
                weights_count = len(header) - 2  # subtract epoch and fitness
                
                # Parse each row
                for line in lines[1:]:
                    parts = line.strip().split(',')
                    epoch = int(parts[0])
                    fitness = float(parts[1])
                    weights = [float(w) for w in parts[2:]]
                    
                    specimen = Specimen(
                        fitness=fitness,
                        weights=weights,
                        heuristic=heuristic_factory(weights),
                        epoch=epoch
                    )
                    champions.append(specimen)
        except FileNotFoundError:
            print(f"File {filename} not found.")
        
        return champions
if __name__=="__main__": 
    
    # GeneticAlgorithm parameters
    weights_count = 5
    x_size = 8
    y_size = 8
    search_depth = 2
    
    # run method parameters
    epochs = 10
    population_size = 30
    current_duels = 5
    hall_duels = 4
    transfer_count = 2
    base_weight = 1.0
    past_weight = 1.5
    current_weight = 1.0
    mutation_rate = 0.15
    mutation_strength = 0.1
    
    duel_search_depth = 3

    gen = GeneticAlgorithm(
        weights_count=weights_count,
        x_size=x_size,
        y_size=y_size,
        search_depth=search_depth
    )
    
    final_hall_of_fame = gen.run(
        epochs=epochs,
        population_size=population_size,
        current_duels=current_duels,
        hall_duels=hall_duels,
        transfer_count=transfer_count,
        base_weight=base_weight,
        past_weight=past_weight,
        current_weight=current_weight,
        x_size=x_size,
        y_size=y_size,
        mutation_rate=mutation_rate,
        mutation_strength=mutation_strength
    )
    

    gen.final_showdown(final_hall_of_fame, duels_search_depth=duel_search_depth) 

