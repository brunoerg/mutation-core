import subprocess
import os
import traceback

from src.report import generate_report


# False == mutant killed
def run(command):
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=False, shell=True)
        return True
    except subprocess.CalledProcessError:
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

def analyze(folder_path, command="", jobs=0):
    killed = []
    not_killed = []

    with open(os.path.join(folder_path, 'original_file.txt'), 'r') as file:
        target_file_path = file.readline()

    if command == "":
        build_command = "rm -rf build && cmake -B build && cmake --build build"
        print(f"\n\nRunning {build_command}")
        run(build_command)
        command = get_command_to_kill(target_file_path, jobs)

    try:
        # Get list of files in the folder
        files = [f for f in os.listdir(folder_path)
                 if os.path.isfile(os.path.join(folder_path, f))]

        # Loop through each file in the folder
        len_files = len(files)
        print(f"* {len(files)-1} MUTANTS *")
        i = 0
        for file_name in files:
            if '.txt' in file_name:
                continue
            print(f"[{i+1}/{len_files-1}] Analyzing {file_name}")
            # Construct the full file path
            file_path = os.path.join(folder_path, file_name)

            # Read the content of the current file
            with open(file_path, 'r') as file:
                content = file.read()

            # Replace the content of the target file
            with open(target_file_path, 'w') as target_file:
                target_file.write(content)

            print(f"Running: {command}")
            result = run(command)
            if result:
                print("NOT KILLED ❌")
                not_killed.append(file_name)
            else:
                print("KILLED ✅")
                killed.append(file_name)
            i += 1

    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")

    score = len(killed) / (len(killed) + len(not_killed))
    print(f"\nMUTATION SCORE: {round(score * 100, 2)}%\n")
    generate_report(not_killed, folder_path, target_file_path, score)
    return killed, not_killed
