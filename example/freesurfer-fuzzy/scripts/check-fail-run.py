import tarfile
import os
import argparse
import glob

# Define the path to the .tgz archive and the file to check within the archive
archive_path = "path/to/archive.tgz"
file_to_check = "scripts/recon-all.done"


def get_archives(directory):
    archives = glob.glob(os.path.join(directory, "*.tgz"))
    return archives


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


def parse_args():
    parser = argparse.ArgumentParser("check-fail-run")
    parser.add_argument(
        "--directory",
        required=True,
        help="Path to the directory containing the .tgz archive",
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    # Call the function and print the result
    archives = get_archives(args.directory)
    for archive_path in archives:
        if not check_file_in_tgz(archive_path, file_to_check):
            print(archive_path, "does not contain", file_to_check)


if __name__ == "__main__":
    main()
