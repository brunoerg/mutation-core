import os
import subprocess
import json

def report(not_killed_mutants=[], folder="", original_file=""):
    # Define the JSON structure
    report_data = {
        "filename": original_file,
        "diffs": []
    }

    if "test/" in original_file:
        start_index = original_file.find("test/")
        original_file = original_file[start_index:] if start_index != -1 else None

    subprocess.run(['git', 'checkout', '--', original_file])

    # Iterate over all files in the directory
    for filename in os.listdir(folder):
        if filename in not_killed_mutants:
            modified_file = os.path.join(folder, filename)

            # Use git diff --no-index to compare the files and capture the output
            result = subprocess.run(['git', 'diff', '--no-index', original_file, modified_file], capture_output=True, text=True)

            # Append the diff output to the diffs list
            report_data["diffs"].append(result.stdout)

    # Export the report as a JSON file
    json_file = f'diff_not_killed.json'
    with open(json_file, 'w') as file:
        json.dump(report_data, file, indent=4)

    print(f"Report saved to {json_file}")
