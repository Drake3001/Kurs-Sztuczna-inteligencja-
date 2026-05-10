import subprocess
import csv
import re
import time

# Definiujemy warianty algorytmów i heurystyk do przetestowania
experiments = [
    ("bfs", None),
    ("astar", "lmcut"),
    ("astar", "hff"),
    ("astar", "hadd"),
    ("gbf", "hff"),
    ("gbf", "hadd"),
    ("wastar", "hff"),
    ("ehs", "hff"),
    ("ids", None)
]

domain_file = "zad1/domain.pddl"
problem_file = "zad1/problem.pddl"
csv_filename = "wyniki_eksperymentow.csv"

def run_experiment(search, heuristic):
    cmd = ["python", "-m", "pyperplan", "-s", search]
    if heuristic:
        cmd.extend(["-H", heuristic])
    cmd.extend([domain_file, problem_file])
    
    heuristic_name = heuristic if heuristic else "Brak"
    print(f"[{search.upper()} + {heuristic_name}] Uruchamiam pyperplan...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        
        plan_length_match = re.search(r"Plan length: (\d+)", output)
        nodes_expanded_match = re.search(r"(\d+) Nodes expanded", output)
        search_time_match = re.search(r"Search time: ([\d\.e\+\-]+)", output)
        
        plan_length = plan_length_match.group(1) if plan_length_match else "Brak"
        nodes_expanded = nodes_expanded_match.group(1) if nodes_expanded_match else "Brak"
        
        if search_time_match:
            try:
                search_time = str(round(float(search_time_match.group(1)), 4))
            except ValueError:
                search_time = search_time_match.group(1)
        else:
            search_time = "Brak"
            
        return {
            "Algorytm": search.upper(),
            "Heurystyka": heuristic_name,
            "Dlugosc planu": plan_length,
            "Wezly ekspandowane": nodes_expanded,
            "Czas [s]": search_time
        }
        
    except subprocess.TimeoutExpired:
        print(f"[{search.upper()} + {heuristic_name}] Przekroczono limit czasu (60s)!")
        return {
            "Algorytm": search.upper(),
            "Heurystyka": heuristic_name,
            "Dlugosc planu": "Timeout",
            "Wezly ekspandowane": "Timeout",
            "Czas [s]": ">60"
        }

# Zapisanie do pliku CSV
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=["Algorytm", "Heurystyka", "Dlugosc planu", "Wezly ekspandowane", "Czas [s]"])
    writer.writeheader()
    
    for search, heuristic in experiments:
        res = run_experiment(search, heuristic)
        writer.writerow(res)
        print(f" -> Wynik: {res}\n")

print(f"\nZakończono. Wyniki zapisano do pliku {csv_filename}")
