import re

def parse_coverage_file(coverage_file_path):
    coverage_data = {}
    current_file = None

    # Regular expressions for parsing lines
    file_pattern = re.compile(r"^SF:(.+)$") # Source file
    line_pattern = re.compile(r"^DA:(\d+),(\d+)$") # Line coverage

    with open(coverage_file_path, 'r') as file:
        for line in file:
            line = line.strip()

            # Check for source file
            file_match = file_pattern.match(line)
            if file_match:
                current_file = file_match.group(1)
                coverage_data[current_file] = []
                continue

            # Check for line coverage (DA:line_number,hits)
            line_match = line_pattern.match(line)
            if line_match and current_file:
                line_number = int(line_match.group(1))
                hits = int(line_match.group(2))
                if hits > 0 and line_number not in coverage_data[current_file]:
                    coverage_data[current_file].append(line_number)

    return coverage_data
