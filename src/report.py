from datetime import datetime

import os
import subprocess
import json

def generate_report(not_killed_mutants=[], folder="", original_file="", score=0):
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

    # Export the report as a JSON file
    original_file = original_file.replace(".cpp", "").replace(".py", "").replace("/", "-")
    json_file = f'diff_not_killed-{original_file}.json'
    with open(json_file, 'w') as file:
        json.dump(report_data, file, indent=4)

    print(f"Report saved to {json_file}")
