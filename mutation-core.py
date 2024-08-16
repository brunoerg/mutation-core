#!/usr/bin/env python3

from get_changes import (
    get_changed_files,
    get_lines_touched
)
from gen_mutations import mutate
from analyze import analyze
from report import report

import argparse
import os
import sys
import pathlib

BASE_PATH = str(pathlib.Path().resolve())


def mkdir_mutation_folder(name):
    path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(f'{BASE_PATH}/{name}'):
        os.mkdir(path)

def mutation_core(pr_number=None, file=None, one_mutant=False, only_security_mutations=False, higher_order_mutants=False):
    if file:
        mutate(file, touched_lines=None, pr_number=None, one_mutant=one_mutant, only_security_mutations=only_security_mutations)
        return
    files_changed = get_changed_files(pr_number)
    result = []
    for file in files_changed:
        # Skips mutating test/doc/bench files
        if any(f in file for f in ['test', 'doc', 'bench']) or ('.cpp' not in file and '.h' not in file):
            continue
        lines_touched = get_lines_touched(file)
        result.append({
            "file_path": file,
            "lines_touched": lines_touched
        })
    for item in result:
        mutate(item['file_path'], item['lines_touched'], pr_number, one_mutant, only_security_mutations)

def main():
    parser = argparse.ArgumentParser(description="Tool for applying mutation testing in Bitcoin Core.")
    subparsers = parser.add_subparsers(title="valid subcommands", dest="subcommand")

    parser_mutate = subparsers.add_parser("mutate", help="Create mutants for a specific PR (0 = current branch) or file")
    parser_mutate.add_argument('-p', '--pr', dest="pr", default=0, type=int,
                               help="Bitcoin Core's PR number")
    parser_mutate.add_argument('-f', '--file', dest="file", default="", type=str,
                               help="File path")
    parser_mutate.add_argument('-om', '--one_mutant', dest="one_mutant", default=False, type=bool,
                               help="Generate only one mutant per line")
    parser_mutate.add_argument('-s', '--only_security_mutations', dest="only_security_mutations", default=False, type=bool,
                               help="Apply only security-based mutations (usually to test fuzzing)")
    parser_analyze = subparsers.add_parser("analyze", help="Analyze mutants")
    parser_analyze.add_argument('-f', '--folder', dest="folder", default="", type=str,
                               help="Folder with the mutants")
    parser_analyze.add_argument('-c', '--command', dest="command", default="", type=str,
                               help="Command to test the mutants (e.g. make && ./test/functional/test.py)")

    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
    elif args.subcommand == "mutate":
        if args.pr != 0 and args.file != "":
            sys.exit("You should only provide PR number or file")
        if args.pr != 0:
            mutation_core(pr_number=args.pr, one_mutant=args.one_mutant, only_security_mutations=args.only_security_mutations)
        elif args.file != "":
            mutation_core(file=args.file, one_mutant=args.one_mutant, only_security_mutations=args.only_security_mutations)
        else:
            mutation_core(pr_number=args.pr, one_mutant=args.one_mutant, only_security_mutations=args.only_security_mutations)
    elif args.subcommand == "analyze":
        if args.folder == "" and args.command == "":
            sys.exit("You should provide the folder which contains the mutants and the command to test them")
        analyze_out = analyze(folder_path=args.folder, command=args.command)
    else:
        parser.print_help()
        sys.exit("No command provided.")


if __name__ == "__main__":
    main()