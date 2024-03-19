import argparse
import glob
import json
from logging import root
import os

import joblib
import nibabel
import numpy as np
import tqdm

rootdir = os.path.dirname(os.path.abspath(__file__))
input_entropy_dir = os.path.realpath(os.path.join(rootdir, "../entropy/"))
output_entropy_dir = os.path.realpath(os.path.join(rootdir, "../entropy_compressed/"))
input_json = os.path.realpath(os.path.join(rootdir, "../../json/json_data.json"))


def get_dataset(filename):
    with open(filename, "r") as f:
        dataset = json.load(f)
    return dataset


def load(filename):
    return nibabel.load(filename).get_fdata()


def load_entropy(input_dir, dataset):
    files = glob.glob(input_dir + "/" + dataset + "/*_entropy.nii.gz")
    return np.fromiter(
        (load(file) for file in files), dtype=np.dtype((np.float32, (256, 256, 256)))
    )


def save_entropy(output_dir, subject, entropy):
    np.savez(output_dir + "/" + f"{subject}_entropy.npz", entropy=entropy)


def load_and_save_entropy(subject, input_dir, output_dir):
    entropy = load_entropy(input_dir, subject)
    save_entropy(output_dir, subject, entropy)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=input_json, type=str, help="Input json file")
    parser.add_argument(
        "--input-dir", default=input_entropy_dir, type=str, help="Input directory"
    )
    parser.add_argument(
        "--output-dir", default=output_entropy_dir, type=str, help="Output directory"
    )
    parser.add_argument(
        "--n-jobs", default=20, type=int, help="Number of jobs to run in parallel"
    )
    return parser.parse_args()


def main():

    args = parse_args()
    dataset = get_dataset(args.input)

    os.makedirs(args.output_dir, exist_ok=True)

    with joblib.Parallel(n_jobs=args.n_jobs, verbose=0) as parallel:
        parallel(
            joblib.delayed(load_and_save_entropy)(
                subject, args.input_dir, args.output_dir
            )
            for subject in tqdm.tqdm(dataset["PATNO_id"].values())
        )


if __name__ == "__main__":
    main()
