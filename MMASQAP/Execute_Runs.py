import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path
from datetime import datetime

# Function to execute a hyperparameter tuning scenario
def execute_scenario(path: str, seed: int, id_scenario: int, parallel: int = 1):
    """
    Execute a hyperparameter tuning scenario.

    Args:
        path (str): Path of the scenario.
        seed (int): Random seed.
        id_scenario (int): Scenario ID.
        parallel (int): Number of threads for the scenario.
    """
    scenario_file = path / 'scenario.txt'

    with open(scenario_file, 'a', encoding='utf-8') as file:
        file.write("\n## Scenario ID\n")
        file.write(f"# id_scenario = {id_scenario}\n")
        file.write("\n## Seed\n")
        file.write(f"seed = {seed}\n")
        file.write("\n## Number of threads\n")
        file.write(f"parallel = {parallel}\n")

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Scenario {id_scenario} ready (path = {path})", flush=True)

    log_file = path / 'output.log'
    try:
        with open(log_file, 'w', encoding='utf-8') as log:
            subprocess.run(
                ["Rscript", "execute_irace.R"],
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=path,
                check=True
            )
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Scenario {id_scenario} completed (path = {path})\n", flush=True)
        return True
    except subprocess.CalledProcessError:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Scenario {id_scenario} failed (check = {log_file})\n", flush=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Execute irace batch scenarios with multiple seeds and optional parallelization."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[
            100001, 200009, 300025, 400049, 500081,
            600121, 700169, 800225, 900289, 100361,
            110411, 120529, 130625, 140729, 150841,
            160961, 171089, 181225, 191369, 201521
        ],
        help="Random seeds for testing (default: 20 predefined seeds)"
    )
    parser.add_argument(
        "--parallel-python",
        type=int,
        default=1,
        help="Maximum number of simultaneous Python executions (default: 1)"
    )
    parser.add_argument(
        "--parallel-irace",
        type=int,
        default=1,
        help="Number of parallel threads for each irace execution (default: 1)"
    )
    
    args = parser.parse_args()

    seeds = args.seeds
    max_parallel_python = args.parallel_python
    parallel_irace = args.parallel_irace

    # Directories for base scenarios, destination and scenario names
    directories = [
        ('Scenarios/BLHS-BL/Base', 'Scenarios/BLHS-BL/Runs', 'BLHS-BL'),
        ('Scenarios/CHAOS-BL/Base', 'Scenarios/CHAOS-BL/Runs', 'CHAOS-BL'),
        ('Scenarios/SOBOL-BL/Base', 'Scenarios/SOBOL-BL/Runs', 'SOBOL-BL'),
        ('Scenarios/UNIF-BL/Base', 'Scenarios/UNIF-BL/Runs', 'UNIF-BL'),
        ('Scenarios/BLHS-BH/Base', 'Scenarios/BLHS-BH/Runs', 'BLHS-BH'),
        ('Scenarios/CHAOS-BH/Base', 'Scenarios/CHAOS-BH/Runs', 'CHAOS-BH'),
        ('Scenarios/SOBOL-BH/Base', 'Scenarios/SOBOL-BH/Runs', 'SOBOL-BH'),
        ('Scenarios/UNIF-BH/Base', 'Scenarios/UNIF-BH/Runs', 'UNIF-BH'),
    ]

    # List to store data for each run
    runs_data = []
    # Generate combinations of base scenarios and seeds
    for base_str, dest_str, scenary_type in directories:
        # Verify existence of base directory
        base_dir = Path(base_str)
        dest_dir = Path(dest_str)
        if not base_dir.exists():
            raise FileNotFoundError(f"The base directory '{base_dir}' does not exist.")
        # ID that represents the run for each combination of scenario and seed
        run_id = 1
        # Create destination directory if it doesn't exist for each scenario-seed combination
        for seed in seeds:
            # Create a unique path for each scenario-seed combination
            path = dest_dir / f"{scenary_type}_seed_{seed}"
            path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(base_dir, path, dirs_exist_ok=True)
            runs_data.append((path, seed, run_id))
            run_id += 1

    # Total number of scenarios to run
    N = len(runs_data)

    print("Irace Experimental Batch Execution\n")
    print(f"Total number of scenarios: {N}")
    print(f"Maximum number of simultaneous executions: {max_parallel_python}")
    print(f"Number of threads for each scenario: {parallel_irace}\n")

    print(f"Executing {N} irace runs across all scenarios...\n", flush=True)

    successful_runs = 0
    failed_runs = 0

    try:
        # Execute scenarios in parallel
        with ThreadPoolExecutor(max_workers=max_parallel_python) as executor:
            futures = {
                executor.submit(execute_scenario, path, seed, id_scenario, parallel_irace): (path, id_scenario) 
                for path, seed, id_scenario in runs_data
            }
            
            for future in as_completed(futures):
                path, id_scenario = futures[future]
                try:
                    success = future.result()
                    if success:
                        successful_runs += 1
                    else:
                        failed_runs += 1
                except Exception as e:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Exception in Scenario {id_scenario}: {e}")
                    failed_runs += 1

    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
        executor.shutdown(wait=False, cancel_futures=True)
        return

    print("Execution Summary")
    print(f"Successful runs: {successful_runs}")
    print(f"Failed runs: {failed_runs}")


if __name__ == "__main__":
    main()