import argparse
import json
import subprocess
import os
from joblib import Parallel, delayed


def parse_args():
    parser = argparse.ArgumentParser("run-base-template")
    parser.add_argument("--input", default="json_data_base.json")
    parser.add_argument("--script", required=True, help="Script to run")
    args = parser.parse_args()
    return args


def make_args(script, first_visit, second_visit, output_dir):
    script = os.path.realpath(script)
    if not os.path.exists(script):
        raise FileNotFoundError(script)

    args = []
    for patno in first_visit.keys():
        visit1 = first_visit[patno]
        visit2 = second_visit[patno]
        output = output_dir[patno]

        args.append((script, visit1, visit2, output))

    return args


def run_script(*args):
    subprocess.run(list(args), check=False, text=True, capture_output=True)


def main():
    args = parse_args()

    with open(args.input) as fi:
        maps = json.load(fi)

    script_args = make_args(
        args.script, maps["first_visit"], maps["second_visit"], maps["PATNO_base"]
    )

    Parallel(n_jobs=-1)(delayed(run_script)(*sarg) for sarg in script_args)


main()
