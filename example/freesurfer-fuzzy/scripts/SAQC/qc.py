import argparse
import glob
import itertools
import json
import logging
import os
import tarfile
import tempfile
from argparse import Namespace
from typing import Any, Literal

import nibabel as nib
import numpy as np
from joblib import Memory, Parallel, delayed
from nibabel.filebasedimages import FileBasedImage
from nibabel.freesurfer.mghformat import MGHImage
from nibabel.nifti1 import Nifti1Image
from numpy.typing import NDArray

logger: logging.Logger = logging.getLogger("QC")
logging.basicConfig(level=logging.INFO)


NImage = Nifti1Image | MGHImage


def load_mgz_file(
    file_path: str, show_labels: bool = False, index: int = 0
) -> NImage | None:
    try:
        logger.debug("Load file: %s", file_path)
        img: FileBasedImage = nib.load(file_path)
        if isinstance(img, NImage):
            print_info_image(img, index, show_labels)
            return img
        else:
            return None
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return None


def print_info_image(
    segmentation: NImage, segmentation_id: int, show_labels: bool
) -> None:
    logger.debug("Segmentation %d: %s", segmentation_id, segmentation.get_filename())
    logger.debug(" - shape: %s", segmentation.shape)
    logger.debug(" - affine: %s", segmentation.affine)
    if show_labels:
        labels: NDArray = np.unique(segmentation.get_fdata())
        logger.debug(" - #labels: %s", labels.size)
        logger.debug(" - labels: %s", labels)


def dice_coefficient(segmentation1: NImage, segmentation2: NImage) -> float:
    """Compute Dice Coefficient, a measure of overlap between two segmentations."""

    logger.debug("Compute Dice Coefficient for two segmentations.")

    segmentation1_data: np.ndarray = segmentation1.get_fdata()
    segmentation2_data: np.ndarray = segmentation2.get_fdata()

    if segmentation1_data.shape != segmentation2_data.shape:
        raise ValueError(
            "Shape mismatch: segmentation1 and segmentation2 must have the same shape."
        )

    intersection = np.equal(segmentation1_data, segmentation2_data)
    return (
        2.0 * intersection.sum() / (segmentation1_data.sum() + segmentation2_data.sum())
    )


def compare_multiple_segmentations(
    file_paths: list[str], show_labels: bool
) -> NDArray[Any] | Literal["Error in loading files"]:
    segmentations: list[NImage | None] = [
        load_mgz_file(file_path, show_labels, i)
        for (i, file_path) in enumerate(file_paths, start=1)
    ]
    if any(seg is None for seg in segmentations):
        return "Error in loading files"

    pairwise_comparisons = {}
    for (i, seg1), (j, seg2) in itertools.combinations(enumerate(segmentations), 2):
        if seg1 is not None and seg2 is not None:
            dice_score: float = dice_coefficient(seg1, seg2)
            pairwise_comparisons[(i, j)] = dice_score

    return np.array(list(pairwise_comparisons.values()))


# Main function to process the subject data
def process_subject(
    tar_subjects, cache_directory, filename, show_labels
) -> NDArray[Any] | None:
    memory = Memory(cache_directory, verbose=0)
    cached_comparison = memory.cache(
        compare_multiple_segmentations, ignore=["show_labels"]
    )

    mgz_files = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for tar_subject in tar_subjects:
            subject: str = os.path.basename(tar_subject).split(".")[0]
            repetition: str = os.path.basename(os.path.dirname(tar_subject))
            archive_path: str = tar_subject
            try:
                with tarfile.open(archive_path, "r:gz") as tar:
                    segmentation_path: str = f"{subject}/mri/{filename}"
                    new_segmentation_path: str = f"{repetition}_{filename}"
                    tar.extract(segmentation_path, path=temp_dir)
                    src: str = os.path.join(temp_dir, segmentation_path)
                    dst: str = os.path.join(temp_dir, new_segmentation_path)
                    os.rename(src, dst)
                    mgz_files.append(dst)
            except tarfile.ReadError as e:
                logger.error(f"Error extracting file {archive_path}: {e}")

        # Compare segmentations and cache the result
        comparison_results = cached_comparison(mgz_files, show_labels)

        return comparison_results


def get_tarfiles(directory, subject) -> list[str]:
    """Get tarfile paths for all repetitions in a directory given a subject."""
    regexp: str = os.path.join(directory, "rep*", f"{subject}.tgz")
    logger.debug("Search path for tar files: %s", regexp)
    return glob.glob(regexp, recursive=True)


def compute_stats(pairwise_comparisons) -> dict[str, np.float64]:
    """Compute stats for Dice Coefficient scores."""
    return {
        "mean": np.mean(pairwise_comparisons),
        "median": np.median(pairwise_comparisons),
        "min": np.min(pairwise_comparisons),
        "max": np.max(pairwise_comparisons),
        "std": np.std(pairwise_comparisons, dtype=np.float64),
    }


def print_info(
    stats: dict[str, np.float64], subject: str, collect_output: list | None
) -> None:
    """Print information about the Dice Coefficient scores."""
    if collect_output is None:
        logger.info("Subject                : %s", subject)
        logger.info("Mean   Dice Coefficient: %.3e", stats["mean"])
        logger.info("Median Dice Coefficient: %.3e", stats["median"])
        logger.info("Min    Dice Coefficient: %.3e", stats["min"])
        logger.info("Max    Dice Coefficient: %.3e", stats["max"])
        logger.info(
            "Std    Dice Coefficient: %.3e",
            stats["std"],
        )
    else:
        msg: str = f"Subject                : {subject}\n"
        msg += f"Mean   Dice Coefficient: {stats['mean']:.3e}\n"
        msg += f"Median Dice Coefficient: {stats['median']:.3e}\n"
        msg += f"Min    Dice Coefficient: {stats['min']:.3e}\n"
        msg += f"Max    Dice Coefficient: {stats['max']:.3e}\n"
        msg += f"Std    Dice Coefficient: {stats['std']:.3e}\n"
        collect_output.append(msg)


def dump_stats(stats, cache_directory) -> None:
    """Dump stats to file."""
    stats_path: str = os.path.join(cache_directory, "stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)


def parse_args() -> Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare segmentations using Dice Coefficient."
    )
    parser.add_argument(
        "--directory",
        type=str,
        help="Directory containing segmentation files to compare.",
    )
    parser.add_argument("--subjects", action="append", default=[], help="Subject ID.")
    parser.add_argument(
        "--subjects-file", type=str, help="File containing subject IDs."
    )
    parser.add_argument(
        "--filename",
        type=str,
        default="aparc.a2009s+aseg.mgz",
        help="Filename of segmentation files to compare.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output.")
    parser.add_argument(
        "--cache-directory", type=str, default="cache", help="Cache directory"
    )
    parser.add_argument("--show-labels", action="store_true", help="Show labels.")
    parser.add_argument("--n-jobs", type=int, default=1, help="Number of jobs.")
    args: Namespace = parser.parse_args()
    return args


def process_single_subject(subject, args):
    collect_output = []  # List to accumulate outputs

    # Replace print statements with appending to the output list
    collect_output.append(f"Processing subject: {subject}")

    file_paths: list[str] = get_tarfiles(args.directory, subject)
    dice_scores: NDArray[Any] | None = process_subject(
        file_paths, args.cache_directory, args.filename, args.show_labels
    )
    subject_stats: dict[str, np.float64] = compute_stats(dice_scores)

    # Accumulate information to be printed
    print_info(
        subject_stats, subject, collect_output
    )  # Assume this function formats the info

    return (
        subject,
        subject_stats,
        "\n".join(collect_output),
    )  # Return accumulated output as a single string


def main() -> None:
    args: Namespace = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.subjects_file and args.subjects:
        raise ValueError("Please provide either --subjects or --subjects-file.")

    if args.subjects_file:
        with open(args.subjects_file, "r") as f:
            args.subjects = f.read().splitlines()

    subjects: list[str] = args.subjects
    stats: dict[str, dict[str, np.float64]] = {}

    results: list[Any] | None = Parallel(n_jobs=args.n_jobs)(
        delayed(process_single_subject)(subject, args) for subject in subjects
    )

    if results is None:
        raise ValueError("No results returned.")

    for subject, subject_stats, subject_info in results:
        stats[subject] = subject_stats
        print(subject_info)

    dump_stats(stats, args.cache_directory)


if __name__ == "__main__":
    main()
