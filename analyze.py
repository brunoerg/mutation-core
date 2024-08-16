import subprocess
import os

from report import report

# False == mutant killed
def run(command):
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False


def analyze(folder_path, command=""):
    killed = []
    not_killed = []
    
    with open(os.path.join(folder_path, 'original_file.txt'), 'r') as file:
        target_file_path = file.readline()

    try:
        # Get list of files in the folder
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        # Loop through each file in the folder
        len_files = len(files)
        print(f"* {len(files)} MUTANTS *")
        i = 0
        for file_name in files:
            if '.txt' in file_name:
                continue
            print(f"[{i}/{len_files}] Analyzing {file_name}")
            # Construct the full file path
            file_path = os.path.join(folder_path, file_name)

            # Read the content of the current file
            with open(file_path, 'r') as file:
                content = file.read()

            # Replace the content of the target file
            with open(target_file_path, 'w') as target_file:
                target_file.write(content)

            result = run(command)
            if result:
                print("NOT KILLED ❌")
                not_killed.append(file_name)
            else:
                print("KILLED ✅")
                killed.append(file_name)
            i += 1

    except Exception as e:
        print(f"An error occurred: {e}")

    score = len(killed) / (len(killed) + len(not_killed))
    print(f"MUTATION SCORE: {score}")
    report(not_killed, folder_path, target_file_path)
    return killed, not_killed