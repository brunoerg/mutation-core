#!/usr/bin/env python3

from src.get_changes import (
    get_changed_files,
    get_lines_touched
)
from src.gen_mutations import mutate
from src.analyze import analyze
from src.cov import parse_coverage_file

import argparse
import os
import json
import sys
import pathlib

BASE_PATH = str(pathlib.Path().resolve())


def mkdir_mutation_folder(name):
    path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(f'{BASE_PATH}/{name}'):
        os.mkdir(path)

def read_json_dict(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: File '{filename}' contains invalid JSON.")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}


def mutation_core(pr_number=None, file=None, one_mutant=False,
                  only_security_mutations=False, range_lines=None,
                  cov=None, test_only=False, skip_lines=None):
    if cov:
        cov = parse_coverage_file(cov)
    if file:
        is_unit_test = 'test' in file and 'py' not in file
        mutate(file, touched_lines=None, pr_number=None,
               one_mutant=one_mutant, only_security_mutations=only_security_mutations,
               range_lines=range_lines, cov=cov, is_unit_test=is_unit_test, skip_lines=skip_lines)
        return
    files_changed = get_changed_files(pr_number)
    result = []
    for file_changed in files_changed:
        # Skips mutating test/bench files
        if any(f in file_changed for f in ['doc', 'fuzz', 'bench', 'util']) or '.txt' in file_changed:
            continue
        lines_touched = get_lines_touched(file_changed)
        is_unit_test = 'test' in file_changed and ('py' not in file_changed and 'util' not in file_changed)
        if test_only and not (is_unit_test or '.py' in file_changed):
            continue
        result.append({
            "file_path": file_changed,
            "lines_touched": lines_touched,
            "is_unit_test": is_unit_test
        })
    for item in result:
        mutate(file_to_mutate=item['file_path'], touched_lines=item['lines_touched'],
               pr_number=pr_number, one_mutant=one_mutant,
               only_security_mutations=only_security_mutations,
               cov=cov, is_unit_test=item["is_unit_test"], skip_lines=skip_lines)


def main():
    parser = argparse.ArgumentParser(description="Mutation testing tool designed for Bitcoin Core.")
    subparsers = parser.add_subparsers(title="valid subcommands", dest="subcommand")

    parser_mutate = subparsers.add_parser("mutate", help="Create mutants for a specific PR (0 = current branch) or file")
    parser_mutate.add_argument('-p', '--pr', dest="pr", default=0, type=int,
                               help="Bitcoin Core's PR number")
    parser_mutate.add_argument('-t', '--test-only', dest="test_only", default=False, type=bool,
                               help="Only create mutants for unit and functional tests")
    parser_mutate.add_argument('-c', '--cov', dest="cov", default="", type=str,
                               help="Path for the coverage file (*.info generated with cmake -P build/Coverage.cmake)")
    parser_mutate.add_argument('-sl', '--skip_lines', dest="skip", default="", type=str,
                               help="Path for the file with lines to skip when creating mutants")
    parser_mutate.add_argument('-f', '--file', dest="file", default="", type=str,
                               help="File path")
    parser_mutate.add_argument('-r', '--range', dest="range_lines", type=int, default=None, nargs=2,
                               help="Specify a range of lines from a file to be mutated")
    parser_mutate.add_argument('-om', '--one_mutant', dest="one_mutant", default=False, type=bool,
                               help="Create only one mutant per line (default=0)")
    parser_mutate.add_argument('-s', '--only_security_mutations', dest="only_security_mutations", default=False, type=bool,
                               help="Apply only security-based mutations (usually to test fuzzing, default=0)")
    parser_analyze = subparsers.add_parser("analyze", help="Analyze mutants")
    parser_analyze.add_argument('-f', '--folder', dest="folder", default="", type=str,
                               help="Folder with the mutants")
    parser_analyze.add_argument('-t', '--timeout', dest="timeout", default=1000, type=int,
                               help="Timeout value per mutant")
    parser_analyze.add_argument('-j', '--jobs', dest="jobs", default=0, type=int,
                               help="Number of jobs to be used to compile Bitcoin Core")
    parser_analyze.add_argument('-c', '--command', dest="command", default="", type=str,
                               help="Command to test the mutants (e.g. cmake --build build && ./build/test/functional/test.py)")
    parser_analyze.add_argument('-st', '--survival-threshold', dest="survival_threshold", default=0.75, type=float,
                               help="Maximum acceptable survival rate (0.3 = 30%)")

    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
    elif args.subcommand == "mutate":
        if args.skip:
            args.skip = read_json_dict(args.skip)
            if args.skip == {}:
                sys.exit()
        if args.cov != "" and args.range_lines is not None:
            sys.exit("You should only provide coverage file or the range of lines to mutate")
        if args.pr != 0 and args.file != "":
            sys.exit("You should only provide PR number or file")
        if args.pr != 0:
            mutation_core(pr_number=args.pr, one_mutant=args.one_mutant,
                          only_security_mutations=args.only_security_mutations,
                          cov=args.cov, test_only=args.test_only, skip_lines=args.skip)
        elif args.file != "":
            range_lines = args.range_lines
            if range_lines:
                if range_lines[0] > range_lines[1]:
                    sys.exit("Invalid range")
            mutation_core(file=args.file, one_mutant=args.one_mutant, only_security_mutations=args.only_security_mutations,
                          range_lines=range_lines, cov=args.cov, skip_lines=args.skip)
        else:
            mutation_core(pr_number=args.pr, one_mutant=args.one_mutant, only_security_mutations=args.only_security_mutations,
                          cov=args.cov, test_only=args.test_only, skip_lines=args.skip)
    elif args.subcommand == "analyze":
        # When the folder is not specified, try to find all muts* folder
        if args.folder == "":
            folders_starting_with_muts = []
            for root, dirs, _ in os.walk('.'):
                for folder in dirs:
                    if folder.startswith("muts"):
                        folders_starting_with_muts.append(os.path.join(root, folder))
            for folder in folders_starting_with_muts:
                analyze(folder_path=folder, command=args.command, jobs=args.jobs, timeout=args.timeout, survival_threshold=args.survival_threshold)
        else:
            analyze(folder_path=args.folder, command=args.command, jobs=args.jobs, timeout=args.timeout, survival_threshold=args.survival_threshold)
    else:
        parser.print_help()
        sys.exit("No command provided.")


if __name__ == "__main__":
    main()
