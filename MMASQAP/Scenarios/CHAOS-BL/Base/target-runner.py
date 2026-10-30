#!/usr/bin/python3

import subprocess
import sys
import os
import re
import glob

def error(message):
    print(f"{os.popen('date').read().strip()}: error: {message}", file=sys.stderr)
    sys.exit(1)

# Path to the irace executable
EXE = "../../../../../Code/mmasqap"

# Fixed parameters for ILS
FIXED_PARAMS = " --trials 1 --iterations 1 --evaluations 5000 "

# Ensure sufficient arguments are provided
if len(sys.argv) < 5:
    error("Not enough arguments provided. Expected at least 4 arguments.")

# Extract main arguments
CONFIG_ID = sys.argv[1]
INSTANCE_ID = sys.argv[2]
SEED = sys.argv[3]
INSTANCE = sys.argv[4]

# Collect dynamic parameters
CONFIG_PARAMS = " ".join(sys.argv[5:])

# Generate output filenames
STDOUT = f"c{CONFIG_ID}-{INSTANCE_ID}-{SEED}.stdout"
STDERR = f"c{CONFIG_ID}-{INSTANCE_ID}-{SEED}.stderr"

# Check if the executable exists and is executable
if not os.path.exists(EXE) or not os.access(EXE, os.X_OK):
    error(f"{EXE}: not found or not executable (pwd: {os.getcwd()})")

# Build the command line
command = f"{EXE} {FIXED_PARAMS} -i {INSTANCE} --seed {SEED} {CONFIG_PARAMS}"

# Execute the command
try:
    with open(STDOUT, 'w') as stdout_file, open(STDERR, 'w') as stderr_file:
        subprocess.run(command, shell=True, stdout=stdout_file, stderr=stderr_file, check=True)
except subprocess.CalledProcessError as e:
    error(f"Command failed with error: {e}")

# Check if the stdout file exists and is not empty
if not os.path.isfile(STDOUT) or os.path.getsize(STDOUT) == 0:
    error(f"{STDOUT}: No such file or is empty")

# Extract the best objective value from the output file
try:
    with open(STDOUT, 'r') as file:
        output = file.readlines()
        last_line = output[-1].strip()
        cost = int(last_line.split()[-1])  # Adjust parsing as needed
except Exception as e:
    error(f"Failed to parse output: {e}")

# Print the extracted cost
print(cost)

# Clean up temporary files
os.remove(STDOUT)
os.remove(STDERR)
for pattern in ["*.sum", "*.rep"]:
    files = glob.glob(pattern)
    for file in files:
        try:
            os.remove(file)
        # Avoid to delete inexistence file
        except FileNotFoundError:
            pass
