import os
import re
import json
import subprocess
from datetime import datetime

def get_git_hash():
    try:
        result = subprocess.run(['git', 'log', '--pretty=format:%h', '-n', '1'],
                              capture_output=True,
                              text=True,
                              check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting git hash: {e}")
        return None


def parse_diffs_to_json(diffs_list):
    result = {}

    for diff in diffs_list:
        match = re.search(r'@@ -(\d+),', diff)
        if match:
            line_num = str(int(match.group(1)) + 3)
            if line_num not in result:
                result[line_num] = []

            commit = get_git_hash()
            result[line_num].append({
                "id": len(result[line_num]) + 1,
                "commit": commit if commit else "",
                "diff": diff[diff.index("@@"):],
                "status": "alive"
            })

    return result

def generate_report(not_killed_mutants=[], folder="", original_file="", score=0.00, just_append=True):
    # Skips creating a report file if mutation score is 100%
    if len(not_killed_mutants) == 0:
        return

    now = datetime.now()
    # Define the JSON structure
    report_data = {
        "filename": original_file,
        "mutation_score": score,
        "date": now.strftime("%d/%m/%Y %H:%M:%S"),
        "diffs": []
    }

    if "test/" in original_file and ".cpp" not in original_file:
        start_index = original_file.find("test/")
        original_file = original_file[start_index:] if start_index != -1 else None

    subprocess.run(['git', 'checkout', '--', original_file])
    print("Surviving mutants:")
    # Iterate over all files in the directory
    for filename in os.listdir(folder):
        if filename in not_killed_mutants:
            modified_file = os.path.join(folder, filename)

            # Use git diff --no-index to compare the files and capture the output
            result = subprocess.run(['git', 'diff', '--no-index',
                                     original_file, modified_file],
                                     capture_output=True, text=True)
            print(result.stdout)
            print("--------------")

            # Append the diff output to the diffs list
            report_data["diffs"].append(result.stdout)

    report_data["diffs"] = parse_diffs_to_json(report_data["diffs"])

    # Check if we should append to an existing file or create a new one
    json_file = 'diff_not_killed.json' if just_append else f'diff_not_killed-{original_file.replace(".cpp", "").replace(".py", "").replace("/", "-")}.json'

    if just_append and os.path.exists(json_file):
        # Load existing data if the file exists
        with open(json_file, 'r', errors='ignore') as file:
            existing_data = json.load(file)
        if isinstance(existing_data, list):
            existing_data.append(report_data)
        else:
            existing_data = [existing_data, report_data]
    else:
        # Start with fresh data
        existing_data = [report_data] if just_append else report_data

    # Save to the JSON file
    with open(json_file, 'w') as file:
        json.dump(existing_data, file, indent=4)
