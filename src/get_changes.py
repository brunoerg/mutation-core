import subprocess


def run_git_command(cmd):
    """Run a git command and capture its output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        return False


def get_changed_files(pr_number=None):
    if pr_number:
        """Get the list of files changed in the pull request."""
        cmd = ['git', 'fetch', 'upstream', f'pull/{pr_number}/head:pr/{pr_number}']
        git_run = run_git_command(cmd)
        if git_run == False:
            print("Fetching and updating branch...")
            cmd = ['git', 'rebase', f'pr/{pr_number}']
        else:
            print("Checking out...")
            cmd = ['git', 'checkout', f'pr/{pr_number}']
            run_git_command(cmd)

    cmd = ['git', 'diff', '--name-only', 'upstream/master...HEAD']
    files = run_git_command(cmd)
    return files


def get_lines_touched(file_path):
    """Get the lines touched in a specific file of the pull request."""
    cmd = ['git', 'diff', '--unified=0', 'upstream/master...HEAD', '--', file_path]
    diff_output = run_git_command(cmd)

    lines = []
    for line in diff_output:
        if line.startswith('@@'):
            parts = line.split(' ')
            for part in parts:
                if part.startswith('+'):
                    line_info = part.split(',')
                    if len(line_info) == 2:
                        start_line = int(line_info[0][1:])
                        num_lines = int(line_info[1])
                        lines.extend(range(start_line, start_line + num_lines))
                    else:
                        lines.append(int(line_info[0][1:]))
    return lines
