#!/usr/bin/env python3

import pathlib
import re
import os

from random import shuffle
from src.operators import (
    REGEX_OPERATORS,
    SECURITY_OPERATORS,
    TEST_OPERATORS
)

BASE_PATH = str(pathlib.Path().resolve())
BASE_MUT = f'{BASE_PATH}/muts'
DO_NOT_MUTATE = ["//",
                 "#",
                 "*",
                 "assert",
                 "self.log",
                 "Assume",
                 "CHECK_NONFATAL",
                 "/*",
                 "LogPrintf",
                 "LogPrint",
                 "strprintf",
                 "G_FUZZING"]

DO_NOT_MUTATE_PY = ["wait_for",
                    "wait_until",
                    "check_",
                    "for",
                    "expected_error",
                    "def",
                    "send_and_ping",
                    "test_",
                    "rehash",
                    "start_",
                    "solve()",
                    "rehash",
                    "restart_",
                    "stop_",
                    "connect_",
                    "sync_",
                    "restart_",
                    "class",
                    "return",
                    "generate("
                    "continue",
                    "sleep",
                    "break",
                    "getcontext().prec",
                    "if",
                    "else",
                    "assert"]

DO_NOT_MUTATE_UNIT = ["while",
                      "for",
                      "if",
                      "test_",
                      "_test",
                      "reset",
                      "class",
                      "return",
                      "continue",
                      "break",
                      "if",
                      "else",
                      "reserve",
                      "resize",
                      "static",
                      "void",
                      "BOOST_",
                      "LOCK(",
                      "LOCK2(",
                      "Test",
                      "Assert",
                      "EXCLUSIVE_LOCKS_REQUIRED",
                      "catch"]

SKIP_IF_CONTAIN = [
    "EnableFuzzDeterminism",
    "nLostUnk",
    "RPCArg::Type::"
]

def mkdir_mutation_folder(name, file_to_mutate):
    path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(f'{BASE_PATH}/{name}'):
        os.mkdir(path)
        file_path = "original_file.txt"
        with open(f'{path}/{file_path}', 'w') as file:
            file.write(file_to_mutate)


def write_mutation(file_to_mutate, lines, i, pr_number=None):
    file_extension = ".cpp"
    if ".h" in file_to_mutate:
        file_extension = ".h"
    if ".py" in file_to_mutate:
        file_extension = ".py"
    file_name = file_to_mutate.split('/')
    file_name = file_name[len(file_name) - 1].split('.')[0]

    folder = "muts"
    ext = file_extension.replace('.', '')
    if pr_number:
        folder = f'muts-pr-{pr_number}-{file_name}-{ext}'
    else:
        folder = folder + f'-{file_name}-{ext}'
    mkdir_mutation_folder(folder, file_to_mutate)
    mutator_file = f'{BASE_PATH}/{folder}/{file_name}.mutant.{i}{file_extension}'
    with open(mutator_file, 'w', encoding="utf8") as file:
        file.writelines(lines)
        return i + 1


def mutate(file_to_mutate="", touched_lines=None, pr_number=None,
           one_mutant=False, only_security_mutations=False,
           range_lines=None, cov=None, is_unit_test=False,
           skip_lines=None):
    print(f"Generating mutants for {file_to_mutate}...")
    input_file = f'{BASE_PATH}/{file_to_mutate}'

    with open(input_file, 'r', encoding="utf8") as source_code:
        source_code = source_code.readlines()

    ALL_OPS = REGEX_OPERATORS
    if only_security_mutations:
        ALL_OPS = SECURITY_OPERATORS
    if (".py" in file_to_mutate) or is_unit_test:
        ALL_OPS = TEST_OPERATORS

    if skip_lines:
        skip_lines = skip_lines[file_to_mutate] if file_to_mutate in skip_lines else None

    touched_lines = touched_lines if touched_lines else list(range(1, len(source_code)))
    if one_mutant:
        shuffle(ALL_OPS)
        shuffle(touched_lines)

    lines_with_test_coverage = []
    if cov:
        for item in cov:
            if file_to_mutate in item:
                lines_with_test_coverage = cov[item]
                break

    i = 0
    for line_num in touched_lines:
        line_num = line_num - 1
        if cov and line_num not in lines_with_test_coverage:
            continue
        if range_lines and (line_num < range_lines[0] or line_num > range_lines[1]):
            continue
        if skip_lines and line_num in skip_lines:
            continue
        lines = source_code.copy()
        line_before_mutation = lines[line_num]

        if line_before_mutation.lstrip().startswith(tuple(DO_NOT_MUTATE)):
            continue
        if any(word in line_before_mutation for word in SKIP_IF_CONTAIN):
            continue
        if ".py" in file_to_mutate or is_unit_test:
            do_not_mutate = any(word in line_before_mutation for word in DO_NOT_MUTATE_PY)
            regex_to_search = re.search(r"^\s*([a-zA-Z_]\w*)\s*=\s*(.+)$", line_before_mutation)
            if is_unit_test:
                do_not_mutate = any(word in line_before_mutation for word in DO_NOT_MUTATE_UNIT)
                regex_to_search = re.search(r"\b(?:[a-zA-Z_][a-zA-Z0-9_:<>*&\s]+)\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\[[^\]]*\])?(?:\.(?:[a-zA-Z_][a-zA-Z0-9_]*)|\->(?:[a-zA-Z_][a-zA-Z0-9_]*))*(?:\s*=\s*[^;]+|\s*\{[^;]+\})\s*", line_before_mutation)
            if do_not_mutate:
                continue
            if regex_to_search:
                continue

        mutation_done = False
        for operator in ALL_OPS:
            if re.search(operator[0], line_before_mutation):
                operators_sub = [operator[1]]
                for op_sub in operators_sub:
                    line_mutated = re.sub(operator[0], op_sub, line_before_mutation.lstrip())
                    lines[line_num] = line_before_mutation[:-len(line_before_mutation.lstrip())] + line_mutated
                    i = write_mutation(file_to_mutate, lines, i, pr_number)
                    if one_mutant:
                        mutation_done = True
                        break
            else:
                continue
            if mutation_done:
                break
    print(f"Generated {i} mutants...")
