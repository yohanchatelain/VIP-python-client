import nibabel as nib
import numpy as np
import itertools
import glob
import argparse
import os
import logging
from nibabel.filebasedimages import FileBasedImage

logger = logging.getLogger("QC")
logging.basicConfig(level=logging.INFO)


def load_mgz_file(file_path):
    try:
        logger.debug("Load file: %s", file_path)
        return nib.load(file_path)
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return None


def dice_coefficient(segmentation1: FileBasedImage, segmentation2: FileBasedImage):
    """Compute Dice Coefficient, a measure of overlap between two segmentations."""

    logger.debug("Compute Dice Coefficient for two segmentations.")
    logger.debug("Segmentation 1 shape: %s", segmentation1.filename)
    logger.debug("Segmentation 2 shape: %s", segmentation2.filename)

    if segmentation1.shape != segmentation2.shape:
        raise ValueError(
            "Shape mismatch: segmentation1 and segmentation2 must have the same shape."
        )

    intersection = np.equal(segmentation1, segmentation2)
    return 2.0 * intersection.sum() / (segmentation1.sum() + segmentation2.sum())


def compare_multiple_segmentations(file_paths):
    segmentations = [load_mgz_file(file_path) for file_path in file_paths]
    if any(seg is None for seg in segmentations):
        return "Error in loading files"

    pairwise_comparisons = {}
    for (i, seg1), (j, seg2) in itertools.combinations(enumerate(segmentations), 2):
        dice_score = dice_coefficient(seg1, seg2)
        pairwise_comparisons[(i, j)] = dice_score

    return np.array(list(pairwise_comparisons.values()))


def get_segmentations_file_paths(directory, subject, filename):
    """Get file paths for all segmentation files in a directory."""
    regexp = os.path.join(directory, "**", subject, "**", filename)
    logger.debug("Search path for segmentation files: %s", regexp)
    return glob.glob(regexp, recursive=True)


def print_info(pairwise_comparisons):
    """Print information about the Dice Coefficient scores."""
    logger.info("Mean Dice Coefficient: %s", np.mean(pairwise_comparisons))
    logger.info("Median Dice Coefficient: %s", np.median(pairwise_comparisons))
    logger.info("Min Dice Coefficient: %s", np.min(pairwise_comparisons))
    logger.info("Max Dice Coefficient: %s", np.max(pairwise_comparisons))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare segmentations using Dice Coefficient."
    )
    parser.add_argument(
        "--directory",
        type=str,
        help="Directory containing segmentation files to compare.",
    )
    parser.add_argument("--subject", type=str, help="Subject ID.")
    parser.add_argument(
        "--filename", type=str, help="Filename of segmentation files to compare."
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output.")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    file_paths = get_segmentations_file_paths(
        args.directory, args.subject, args.filename
    )
    dice_scores = compare_multiple_segmentations(file_paths)
    print_info(dice_scores)


if __name__ == "__main__":
    main()
