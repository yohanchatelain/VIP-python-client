import tarfile
import os
import argparse
import glob
from joblib import Parallel, delayed


# Define the path to the .tgz archive and the file to check within the archive
file_to_check = "recon-all.done"


def get_archives(directory):
    archives = glob.glob(os.path.join(directory, "*.tgz"))
    return archives


def get_directory(directory):
    directories = glob.glob(os.path.join(directory, "sub-*"))
    return directories


# Function to check if a file exists in a tar.gz archive
def check_file_in_tgz(archive_path, unzip_directory, file_to_check):
    try:
        # Open the tar.gz archive
        with tarfile.open(archive_path, "r:gz") as archive:
            # List all members of the archive
            archive_members = [os.path.basename(f) for f in archive.getnames()]
            # Check if the specified file exists in the list
            return file_to_check in archive_members
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def extract_file_from_tgz(archive_path, unzip_directory, file_to_check):
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            archive_names = archive.getnames()
            archive_members = [os.path.basename(f) for f in archive_names]
            # Check if the specified file exists in the list
            if file_to_check in archive_members:
                [file_to_check_fullpath] = [
                    f for f in archive_names if f.endswith(file_to_check)
                ]
                archive.extract(file_to_check_fullpath, path=unzip_directory)
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def has_unzip_directory(unzip_directory, archive_path):
    subject = os.path.splitext(os.path.basename(archive_path))[0]
    unzip_directory = os.path.join(unzip_directory, subject)
    return os.path.isdir(unzip_directory)


def check_file_in_directory(archive_path, unzip_directory, file_to_check):
    subject = os.path.splitext(os.path.basename(archive_path))[0]
    subject_path = os.path.join(unzip_directory, subject)
    # iterate over the directory and check if the file exists
    for _, _, files in os.walk(subject_path):
        if file_to_check in files:
            return True
    return False


def check_failure(archive_path, args):
    if has_unzip_directory(args.unzip_directory, archive_path):
        if not check_file_in_directory(
            archive_path, args.unzip_directory, file_to_check
        ):
            extract_file_from_tgz(archive_path, args.unzip_directory, file_to_check)
        if not check_file_in_directory(
            archive_path, args.unzip_directory, file_to_check
        ):
            return archive_path
    elif not check_file_in_tgz(archive_path, args.unzip_directory, file_to_check):
        return archive_path


def parse_args():
    parser = argparse.ArgumentParser("check-fail-run")
    parser.add_argument(
        "--directory",
        required=True,
        help="Path to the directory containing the .tgz archive",
    )
    parser.add_argument(
        "--unzip-directory",
        required=True,
        help="Path to the directory where to unzip the archive",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--file-to-check", default=file_to_check)
    parser.add_argument("--n-jobs", type=int, default=-1)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    # Call the function and print the result
    archives = get_archives(args.directory)
    res = Parallel(n_jobs=args.n_jobs, verbose=10 if args.verbose else 0)(
        delayed(check_failure)(*sargs) for sargs in [(a, args) for a in archives]
    )
    failed, i = zip(*res)

    for archive_path in failed:
        print(archive_path, "does not contain", file_to_check)


if __name__ == "__main__":
    main()
