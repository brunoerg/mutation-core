import subprocess
import os

def report(not_killed_mutants=[], folder="", original_file=""):
    # Define the filenames
    markdown_file = 'diff_not_killed.md'
    # Initialize a variable to hold the diff output
    diff_content = ""

    subprocess.run(['git', 'checkout', '--', original_file])

    # Iterate over all files in the directory
    for filename in os.listdir(folder):
        if filename in not_killed_mutants:
            modified_file = os.path.join(folder, filename)

            # Use git diff --no-index to compare the files and capture the output
            result = subprocess.run(['git', 'diff', '--no-index', original_file, modified_file], capture_output=True, text=True)

            # Append the diff output to the diff_content
            diff_content += f"## Diff between {original_file} and {filename}\n"
            diff_content += "```diff\n"
            diff_content += result.stdout
            diff_content += "\n```\n"

    # Write the aggregated diff output to a markdown file with proper formatting
    with open(markdown_file, 'w') as file:
        file.write(diff_content)

    print(f"Aggregated diff output with the survived mutants has been written to {markdown_file}")