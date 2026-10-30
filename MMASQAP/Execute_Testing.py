import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path
from datetime import datetime

# Function to execute an elite testing scenario
def execute_elite_testing(path: str, seed: int, run_id: int, parallel_irace: int = 1, configurations_file: str = "configurations.txt"):
    """
    Execute an elite testing scenario with only-test mode.

    Args:
        path (str): Path of the testing scenario.
        seed (int): Random seed.
        run_id (int): Run ID.
        parallel_irace (int): Number of parallel threads for irace.
        configurations_file (str): Name of the configurations file to test.
    """
    scenario_file = path / 'scenario.txt'

    # Append seed and other configurations to scenario.txt
    with open(scenario_file, 'a') as file:
        file.write("\n## Run ID\n")
        file.write(f"# run_id = {run_id}\n")
        file.write("\n## Seed\n")
        file.write(f"seed = {seed}\n")
        file.write("\n## Number of threads\n")
        file.write(f"parallel = {parallel_irace}\n")

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Elite Testing Run {run_id} ready (path = {path})", flush=True)
    
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
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Elite Testing Run {run_id} completed (path = {path})\n", flush=True)
        return True
    except subprocess.CalledProcessError:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Elite Testing Run {run_id} failed (check = {log_file})\n", flush=True)
        return False


def main():
    """
    Main function to orchestrate elite testing executions.
    """
    parser = argparse.ArgumentParser(
        description="Execute elite testing scenarios with multiple seeds and optional parallelization."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="Scenarios/All_Elites/Base",
        help="Path to the base directory containing elite testing configuration (default: Scenarios/All_Elites/Base)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="Scenarios/All_Elites/Runs",
        help="Path to the output directory where runs will be created (default: Scenarios/All_Elites/Runs)"
    )
    parser.add_argument(
        "--scenario-name",
        type=str,
        default="All_Elites",
        help="Name of the scenario for naming runs (default: All_Elites)"
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
        help="Number of simultaneous Python executions (default: 1)"
    )
    parser.add_argument(
        "--parallel-irace",
        type=int,
        default=1,
        help="Number of parallel threads for each irace execution (default: 1)"
    )
    parser.add_argument(
        "--configurations-file",
        type=str,
        default="configurations.txt",
        help="Name of the configurations file to test (default: configurations.txt)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without actually running"
    )

    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    scenario_name = args.scenario_name
    seeds = args.seeds
    max_parallel_python = args.parallel_python
    parallel_irace = args.parallel_irace
    configurations_file = args.configurations_file
    dry_run = args.dry_run

    # Verify existence of base directory
    if not base_dir.exists():
        raise FileNotFoundError(f"The base directory '{base_dir}' does not exist.")
    # Check if configurations.txt exists in base directory
    config_path = base_dir / configurations_file
    if not config_path.exists():
        raise FileNotFoundError(f"The configurations file '{configurations_file}' does not exist in '{base_dir}'.")

    # List to store data for each run
    runs_data = []
    # Create runs directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate runs for each seed
    run_id = 1
    for seed in seeds:
        # Create a unique path for each seed
        run_path = output_dir / f"{scenario_name}_seed_{seed}"
        
        # Skip if directory already exists (avoid overwriting)
        if run_path.exists():
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Skipping {run_path} (already exists)")
            run_id += 1
            continue
        
        # Create directory and copy base files
        run_path.mkdir(parents=True, exist_ok=True)
        shutil.copytree(base_dir, run_path, dirs_exist_ok=True)
        
        runs_data.append((run_path, seed, run_id, configurations_file))
        run_id += 1

    # Total number of runs
    N = len(runs_data)

    print("Elite Testing Configuration\n")
    print(f"Scenario name: {scenario_name}")
    print(f"Configurations file: {configurations_file}")
    print(f"Total number of runs: {N}")
    print(f"Maximum number of simultaneous executions: {max_parallel_python}")
    print(f"Number of parallel threads: {parallel_irace}\n")

    if N == 0:
        print("No new runs to execute (all already exist or no seeds provided).\n")
        return

    if dry_run:
        print("DRY RUN MODE - No executions will be performed.\n")
        print("Runs that would be created:")
        for i, (run_path, seed, run_id, _) in enumerate(runs_data, 1):
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Elite Testing Run {run_id} preview (path = {run_path})")
        print()
        return

    print(f"Executing {N} elite testing runs...\n")

    # Execute scenarios in parallel
    successful_runs = 0
    failed_runs = 0

    try:
        with ThreadPoolExecutor(max_workers=max_parallel_python) as executor:
            futures = {
                executor.submit(execute_elite_testing, run_path, seed, run_id, parallel_irace, configurations_file): (run_path, seed, run_id)
                for run_path, seed, run_id, _ in runs_data
            }

            for future in as_completed(futures):
                run_path, seed, run_id = futures[future]
                try:
                    success = future.result()
                    if success:
                        successful_runs += 1
                    else:
                        failed_runs += 1
                except Exception as e:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  Exception in Elite Testing Run {run_id}: {e}")
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
