import subprocess
import os
import traceback
from src.report import generate_report

def run(command, timeout=10000):
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE, text=False, shell=True,
                      timeout=timeout)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False

def get_command_to_kill(target_file_path, jobs):
    build_command = "cmake --build build"
    if jobs != 0:
        build_command += f' -j{jobs}'
    if "functional" in target_file_path:
        command = f"./build/{target_file_path}"
    elif "test" in target_file_path:
        filename_with_extension = os.path.basename(target_file_path)
        test_to_run = filename_with_extension.rsplit('.', 1)[0]
        command = f"{build_command} && ./build/src/test/test_bitcoin --run_test={test_to_run}"
    else:
        command = f"{build_command} && ./build/src/test/test_bitcoin && CI_FAILFAST_TEST_LEAVE_DANGLING=1 ./build/test/functional/test_runner.py -F"
    return command

def analyze(folder_path, command="", jobs=0, timeout=10000, survival_threshold=0.3):
    """
    Analyze mutants with early termination if too many survive.

    Args:
        folder_path: Path to mutants folder
        command: Test command to run
        jobs: Number of parallel jobs
        timeout: Maximum execution time per mutant
        survival_threshold: Maximum acceptable survival rate (0.3 = 30%)
    """
    num_killed = 0
    not_killed = []

    try:
        # Read target file path
        with open(os.path.join(folder_path, 'original_file.txt'), 'r') as file:
            target_file_path = file.readline()

        # Setup command if not provided
        if command == "":
            build_command = "rm -rf build && cmake -B build && cmake --build build"
            print(f"\n\nRunning {build_command}")
            run(build_command)
            command = get_command_to_kill(target_file_path, jobs)

        # Get list of mutant files
        files = [f for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f)) and not f.endswith('.txt')]

        total_mutants = len(files)
        print(f"* {total_mutants} MUTANTS *")

        if total_mutants == 0: raise Exception(f'No mutants on the provided folder path ({folder_path})')
        else:
            for i, file_name in enumerate(files, 1):
                current_survival_rate = len(not_killed) / (total_mutants)
                if current_survival_rate > survival_threshold:
                    print(f"\nTerminating early: {current_survival_rate:.2%} mutants surviving after {i} iterations")
                    print(f"Survival rate exceeds threshold of {survival_threshold:.0%}")
                    break
                print(f"[{i}/{total_mutants}] Analyzing {file_name}")
                file_path = os.path.join(folder_path, file_name)

                # Read and apply mutant
                with open(file_path, 'r') as file:
                    content = file.read()
                with open(target_file_path, 'w') as target_file:
                    target_file.write(content)

                print(f"Running: {command}")
                result = run(command, timeout)
                if result:
                    print("NOT KILLED ❌")
                    not_killed.append(file_name)
                else:
                    print("KILLED ✅")
                    num_killed = num_killed + 1

            # Always generate report with current results
            score = num_killed / total_mutants
            print(f"\nMUTATION SCORE: {round(score * 100, 2)}%")
            generate_report(not_killed, folder_path, target_file_path, score)
    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")
        raise

    # Restore the file
    run(f"git restore {target_file_path}")

    return num_killed, not_killed
