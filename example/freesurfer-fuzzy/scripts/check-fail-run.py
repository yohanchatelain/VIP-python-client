import tarfile
import os
import argparse
import glob
import tqdm
import logging


logger = logging.getLogger(__name__)
# Define the path to the .tgz archive and the file to check within the archive
file_to_check = "recon-all.done"


def get_archives(directory):
    archives = glob.glob(os.path.join(directory, "*.tgz"))
    return archives


def get_directory(directory):
    directories = glob.glob(os.path.join(directory, "sub-*"))
    return directories


# Function to check if a file exists in a tar.gz archive
def check_file_in_tgz(archive_path, file_to_check):
    try:
        # Open the tar.gz archive
        with tarfile.open(archive_path, "r:gz") as archive:
            # List all members of the archive
            archive_members = [os.path.basename(f) for f in archive.getnames()]
            # Check if the specified file exists in the list
            if file_to_check in archive_members:
                return True
            else:
                return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def has_unzip_directory(unzip_directory, archive_path):
    logger.info("unzip_directory: ", unzip_directory)
    logger.debug("archive_path: ", archive_path)
    subject = os.path.splitext(os.path.basename(archive_path).split("."))[0]
    unzip_directory = os.path.join(unzip_directory, subject)
    logger.debug("unzip_directory full path: ", unzip_directory)
    return os.path.isdir(unzip_directory)


def check_file_in_directory(unzip_directory, file_to_check):
    # iterate over the directory and check if the file exists
    for _, _, files in os.walk(unzip_directory):
        if file_to_check in files:
            return True
    return False


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
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    logger.setLevel(logging.DEBUG)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Call the function and print the result
    archives = get_archives(args.directory)
    logger.debug("archives: ", archives)
    failed = []
    for archive_path in tqdm.tqdm(archives):
        if has_unzip_directory(args.unzip_directory, archive_path):
            if not check_file_in_directory(args.unzip_directory, file_to_check):
                failed.append(archive_path)
        elif not check_file_in_tgz(archive_path, file_to_check):
            failed.append(archive_path)

    for archive_path in failed:
        print(archive_path, "does not contain", file_to_check)


if __name__ == "__main__":
    main()
