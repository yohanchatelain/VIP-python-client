import argparse
import json
import os

import cupy as cp
import numpy as np
import tqdm

rootdir = os.path.dirname(os.path.abspath(__file__))
input_entropy_dir = os.path.realpath(os.path.join(rootdir, "../entropy_compressed/"))
input_json = os.path.realpath(os.path.join(rootdir, "../../json/json_data.json"))
output_std = os.path.realpath(os.path.join(rootdir, "../std_entropy.npz"))


def std_entropy(input_dir, dataset, device):
    path = os.path.join(input_dir, f"{dataset}_entropy.npz")
    with cp.cuda.Device(device):
        entropy_gpu = cp.load(path)["entropy"]
        return cp.mean(cp.std(entropy_gpu, axis=0)).get()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subject", type=str, help="Regular expression to select subjects"
    )
    parser.add_argument("--input", default=input_json, type=str, help="Input json file")
    parser.add_argument(
        "--output", default=output_std, type=str, help="Output npz file"
    )
    parser.add_argument(
        "--input-dir", default=input_entropy_dir, type=str, help="Input directory"
    )
    parser.add_argument("--device", default=1, type=int, help="GPU device")
    return parser.parse_args()


def main():

    args = parse_args()

    if args.subject:
        subjects = [args.subject]
    else:
        with open(args.input, "r") as f:
            dataset = json.load(f)
        subjects = list(dataset["PATNO_id"].values())
    _std = np.asanyarray(
        [
            std_entropy(args.input_dir, subject, args.device)
            for subject in tqdm.tqdm(dataset["PATNO_id"].values())
        ]
    )
    np.savez(args.output, subjects=subjects, std=_std)


if __name__ == "__main__":
    main()
