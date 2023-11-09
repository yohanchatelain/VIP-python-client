import glob
import argparse
import os
import tqdm
import re
from joblib import Parallel, delayed


def glob_file(rep, regexps):
    return glob.glob(os.path.join(rep, *regexps), recursive=True)


def parallel_glob(directory, regexps):
    reps = glob.glob(os.path.join(directory, "rep*"))
    files = Parallel(n_jobs=len(reps), verbose=10)(
        delayed(glob_file)(rep, regexps) for rep in reps
    )
    if files:
        files = sum(files, start=[])
    return files


def check_files(directory, filename):
    regex = re.compile("rep[0-9]+/sub-.+_ses-[^/]+")

    # Build a set with subjects + session
    subjects = parallel_glob(directory, ("**", "sub-*_ses-*"))
    subjects_set = set(regex.findall(path)[0] for path in tqdm.tqdm(subjects))

    # Build a set with subjects + session containing filename
    files = parallel_glob(directory, ("**", filename))
    files_set = set(regex.findall(path)[0] for path in tqdm.tqdm(files))

    missing_subjects = subjects_set - files_set

    return missing_subjects


def parse_args():
    parser = argparse.ArgumentParser("data-check")
    parser.add_argument(
        "--directory", required=True, help="Directory that contains experiments"
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    stats_filenames = ["aseg.stats", "lh.aparc.a2009s.stats", "rh.aparc.a2009s.stats"]
    for filename in stats_filenames:
        missing_subjects = check_files(args.directory, filename)
        print(filename, missing_subjects)


if __name__ == "__main__":
    main()
