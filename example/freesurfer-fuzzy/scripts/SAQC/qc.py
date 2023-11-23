import nibabel as nib
import numpy as np
import itertools
import glob
import argparse


def load_mgz_file(file_path):
    try:
        return nib.load(file_path).get_fdata()
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None


def dice_coefficient(segmentation1, segmentation2):
    """Compute Dice Coefficient, a measure of overlap between two segmentations."""
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
    return glob.glob(directory, f"**/{subject}/**/{filename}", recursive=True)


def print_info(pairwise_comparisons):
    """Print information about the Dice Coefficient scores."""
    print("Mean Dice Coefficient:", np.mean(pairwise_comparisons))
    print("Median Dice Coefficient:", np.median(pairwise_comparisons))
    print("Min Dice Coefficient:", np.min(pairwise_comparisons))
    print("Max Dice Coefficient:", np.max(pairwise_comparisons))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare segmentations using Dice Coefficient."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory containing segmentation files to compare.",
    )
    parser.add_argument("subject", type=str, help="Subject ID.")
    parser.add_argument(
        "filename", type=str, help="Filename of segmentation files to compare."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    file_paths = get_segmentations_file_paths(
        args.directory, args.subject, args.filename
    )
    dice_scores = compare_multiple_segmentations(file_paths)
    print_info(dice_scores)


if __name__ == "__main__":
    main()
