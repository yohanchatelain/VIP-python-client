import numpy as np
import nibabel as nib
import glob
import itertools
import os
import tqdm
import monai
    

# Notes
# lh.curv correspond to the curvature of the left hemisphere
# Used by lh.orig as a threshold color 
    

def load_subject(directory, subject, image_name="aparc.a2009s+aseg.mgz"):
    """
    Load all image_name across all repetitions for a subject
    """
    pattern = os.path.join(directory, "rep*", subject, "mri", image_name)
    return np.array([nib.load(img).get_fdata() for img in glob.glob(pattern)])


def compute_similarity(data):
    eq = np.apply_over_axes(np.equal, data, [0])
    similar = np.count_nonzero(eq)
    not_similar = np.count_nonzero(~eq)
    return similar / eq.size


def compute_pairwise_similarity(data):
    """
    Compute similarity between all pairs of images
    """
    return [
        compute_similarity(np.array([data[i], data[j]]))
        for i, j in itertools.combinations(range(len(data)), 2)
    ]


def print_pairwise_similarity_stats(subject, similarities, field, verbose=False):
    _min = np.min(similarities)
    _max = np.max(similarities)
    _mean = np.mean(similarities)
    _median = np.median(similarities)
    _std = np.std(similarities)
    _spread = _max - _min

    if verbose:
        print(f"Mean similarity:    {np.mean(similarities)}")
        print(f"Min similarity:     {np.min(similarities)}")
        print(f"Max similarity:     {np.max(similarities)}")
        print(f"Median similarity:  {np.median(similarities)}")
        print(f"Standard deviation: {np.std(similarities):.3e}")
        print(f"Spread similarity:  {_max - _min:.3e}")

    # print as a csv file
    print(f"{subject},{field},{_mean},{_min},{_max},{_median},{_std},{_spread}")


def dice_coefficient(segmentation1, segmentation2) -> float:
    """Compute Dice Coefficient, a measure of overlap between two segmentations."""

    intersection = np.equal(segmentation1, segmentation2)
    return 2.0 * intersection.sum() / (segmentation1.sum() + segmentation2.sum())


def compare_multiple_segmentations(data):
    return [
        dice_coefficient(seg1, seg2) for seg1, seg2 in itertools.combinations(data, 2)
    ]


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Compute similarity between images")
    parser.add_argument("subject", type=str, help="Subject ID")
    parser.add_argument(
        "--directory", type=str, default=".", help="Directory containing data"
    )
    parser.add_argument(
        "--image_name", type=str, default="aparc.a2009s+aseg.mgz", help="Image name"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    data = load_subject(args.directory, args.subject, args.image_name)
    # print(compute_similarity(data))

    pairwise_sim = compute_pairwise_similarity(data)
    print_pairwise_similarity_stats(args.subject, pairwise_sim, "similarity")

    pairwise_dice = compare_multiple_segmentations(data)
    print_pairwise_similarity_stats(args.subject, pairwise_dice, "dice")


if __name__ == "__main__":
    main()
