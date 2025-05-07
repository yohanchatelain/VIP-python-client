from calendar import c
import os
import numpy as np
import nibabel as nib
from skimage import measure
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import pandas as pd
import plotly as plt
import sklearn.decomposition


def get_default_labels():
    """Return a list of default labels to visualize."""
    return [
        "Left-Accumbens-area",
        "Left-Amygdala",
        "Left-Caudate",
        "Left-Hippocampus",
        "Left-Pallidum",
        "Left-Putamen",
        "Left-Thalamus",
        "Left-Lateral-Ventricle",
        "Right-Accumbens-area",
        "Right-Amygdala",
        "Right-Caudate",
        "Right-Hippocampus",
        "Right-Pallidum",
        "Right-Putamen",
        "Right-Thalamus",
        "Right-Lateral-Ventricle",
    ]


def load_aseg(aseg_file):
    """Load aseg.nii file and return the data."""
    if not os.path.exists(aseg_file):
        raise FileNotFoundError(f"File not found: {aseg_file}")

    print(f"Loading {aseg_file}...")
    img = nib.load(aseg_file)
    data = img.get_fdata()
    affine = img.affine
    return data, affine


def get_freesurfer_label_colors():
    """Return a dictionary of FreeSurfer label colors."""
    # This is a simplified version. For a complete list, you would need to reference
    # the official FreeSurfer color LUT
    colors = {
        2: [245, 245, 245],  # Left-Cerebral-White-Matter
        3: [205, 62, 78],  # Left-Cerebral-Cortex
        4: [245, 245, 245],  # Left-Lateral-Ventricle
        10: [245, 245, 245],  # Left-Thalamus
        11: [0, 118, 14],  # Left-Caudate
        12: [236, 13, 176],  # Left-Putamen
        13: [11, 255, 255],  # Left-Pallidum
        17: [221, 226, 68],  # Left-Hippocampus
        18: [220, 216, 20],  # Left-Amygdala
        26: [220, 216, 20],  # Left-Accumbens-area
        41: [245, 245, 245],  # Right-Cerebral-White-Matter
        42: [205, 62, 78],  # Right-Cerebral-Cortex
        43: [245, 245, 245],  # Right-Lateral-Ventricle
        49: [245, 245, 245],  # Right-Thalamus
        50: [0, 118, 14],  # Right-Caudate
        51: [236, 13, 176],  # Right-Putamen
        52: [11, 255, 255],  # Right-Pallidum
        53: [221, 226, 68],  # Right-Hippocampus
        54: [220, 216, 20],  # Right-Amygdala
        58: [220, 216, 20],  # Right-Accumbens-area
    }
    return colors


def get_label_name(aseg_stat, label):
    """Get the name of a label from aseg stats."""
    # Check if the label is in the aseg stats
    if label in aseg_stat["SegId"].values:
        # Get the corresponding row
        row = aseg_stat[aseg_stat["SegId"] == label]
        # Return the structure name
        return row["StructName"].values[0]
    else:
        return f"Unknown Label {label}"


def create_mesh_from_label(aseg_data, label_id, affine=None, step_size=1, smoothing=0):
    """Create a mesh from a specific label in the aseg data.

    Args:
        aseg_data: 3D numpy array with segmentation data
        label_id: ID of the structure to extract
        affine: Transformation matrix
        step_size: Downsampling factor to speed up processing
        smoothing: Smoothing factor (0-1), higher values create smoother surfaces
    """
    # Create binary mask for this label
    label_mask = aseg_data == label_id

    # Skip if no voxels with this label
    if not np.any(label_mask):
        return None

    # Use scikit-image to extract surface mesh
    try:
        # Subsample for faster processing if needed
        if step_size > 1:
            label_mask = label_mask[::step_size, ::step_size, ::step_size]

        # Apply gaussian smoothing if requested
        if smoothing > 0:
            from scipy.ndimage import gaussian_filter

            # Convert to float for gaussian filter
            smooth_mask = label_mask.astype(float)
            # Apply 3D gaussian filter with sigma based on smoothing parameter (0-1)
            # Higher sigma = more smoothing
            sigma = 0.8 * smoothing  # Scale smoothing parameter
            smooth_mask = gaussian_filter(smooth_mask, sigma=sigma)
            # Extract mesh using smoothed data
            verts, faces, _, _ = measure.marching_cubes(smooth_mask, level=0.5)
        else:
            # Regular extraction without smoothing
            verts, faces, _, _ = measure.marching_cubes(label_mask, level=0.5)

        # Apply step size scaling if used
        if step_size > 1:
            verts = verts * step_size

        # Apply affine transformation if provided
        if affine is not None:
            # Add homogeneous coordinate
            verts_homog = np.hstack((verts, np.ones((verts.shape[0], 1))))
            # Apply transformation
            verts = np.dot(verts_homog, affine.T)[:, :3]

        return verts, faces
    except Exception as e:
        print(f"Error creating mesh for label {label_id}: {e}")
        return None


def intensity_to_rgb(colormap, low=0, high=1):
    import plotly.colors as pc

    colorscale = pc.get_colorscale(colormap)
    return pc.sample_colorscale(colorscale, 101, low=low, high=high)


def visualize_aseg(
    aseg_file,
    aseg_stats,
    aseg_rna=None,
    cmap="RdYlGn_r",
    step_size=2,
    opacity=0.7,
    smoothing=0,
):
    """Visualize aseg.nii file with Plotly.

    Args:
        aseg_file: Path to the aseg.nii file
        labels_to_show: List of label IDs to visualize (None = all)
        step_size: Downsampling factor (higher = faster but less detailed)
        opacity: Transparency of the surfaces (0-1)
        smoothing: Smoothing factor (0-1, higher = smoother surfaces)
    """
    # Load aseg data
    aseg_data, affine = load_aseg(aseg_file)

    labels_to_show = aseg_stats["SegId"].tolist()
    default_labels = get_default_labels()
    labels_name = [get_label_name(aseg_stats, label) for label in labels_to_show]
    labels_name = [label for label in labels_name if label in default_labels]

    # Create a figure
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": "surface"}]])

    if aseg_rna is not None:
        if "ROI" in aseg_rna.columns:
            valid_labels = set(labels_name).intersection(set(aseg_rna["ROI"]))
            min_norm = aseg_rna[aseg_rna.ROI.isin(valid_labels)]["r"].min()
            max_norm = aseg_rna[aseg_rna.ROI.isin(valid_labels)]["r"].max()
        else:
            raise KeyError("Column 'ROI' not found in aseg_rna DataFrame.")
    else:
        min_norm = aseg_stats["normMin"].min()
        max_norm = aseg_stats["normMax"].max()

    max_norm = max(max_norm, 0.5)
    print(f"Min norm: {min_norm}, Max norm: {max_norm}")

    # Get color for this label
    colorscale_rgb = intensity_to_rgb(cmap)

    # For each label, create a mesh and add to the figure
    for label_id in labels_to_show:
        label_name = get_label_name(aseg_stats, label_id)
        if label_name not in default_labels:
            print(f"Skipping label {label_name}...")
            continue

        print(f"Processing label {label_id} ({label_name})...")

        # Get mesh for this label with optional smoothing
        mesh_data = create_mesh_from_label(
            aseg_data, label_id, affine, step_size, smoothing
        )

        if mesh_data is None:
            print(f"No data for label {label_id}")
            continue

        verts, faces = mesh_data

        stat = aseg_stats[aseg_stats["SegId"] == label_id]["normMean"].values[0]
        stat_normalized = (stat - min_norm) / (max_norm - min_norm)

        if aseg_rna is not None:
            # Get the ratio N/A value for this label
            if label_name not in aseg_rna["ROI"].values:
                print(f"Label {label_name} not found in aseg_rna")
                ratio = 0
                continue
            ratio = aseg_rna[aseg_rna["ROI"] == label_name]["r"].values[0]
            stat = ratio
            stat_normalized = (stat - min_norm) / (max_norm - min_norm)
            color_rgb = colorscale_rgb[int(stat_normalized * 100)]

        print(
            f"Label {label_name} - Stat: {stat:.2f}, Normalized: {stat_normalized:.2f}"
        )

        # Add mesh to figure
        fig.add_trace(
            go.Mesh3d(
                x=verts[:, 0],
                y=verts[:, 1],
                z=verts[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                color=color_rgb,
                opacity=opacity,
                name=label_name,
                showscale=True,
                hoverinfo="text",
                hovertemplate=f"<b>{label_name}</b><br>Intensity: {stat:.2f}<extra></extra>",
            )
        )

    # Update layout
    fig.update_layout(
        title="FreeSurfer aseg.nii Visualization",
        scene=dict(
            xaxis=dict(title="X"),
            yaxis=dict(title="Y"),
            zaxis=dict(title="Z"),
            aspectmode="data",
        ),
        width=1600,
        height=1200,
        margin=dict(l=0, r=0, b=0, t=30),
    )

    # Add color bar
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(
                colorscale=cmap,
                cmin=min_norm,
                cmax=max_norm,
                color=0,
                size=10,
                colorbar=dict(title="Intensity"),
            ),
            showlegend=False,
        )
    )

    return fig


def parse_aseg_stats(aseg_stats):
    """Parse aseg stats and return a list of label IDs."""
    columns = [
        "Index",
        "SegId",
        "NVoxels",
        "Volume_mm3",
        "StructName",
        "normMean",
        "normStdDev",
        "normMin",
        "normMax",
        "normRange",
    ]
    df = pd.read_csv(
        aseg_stats, sep=r"\s+", comment="#", names=columns, engine="python"
    )
    return df


def parse_aseg_rna(aseg_rna):
    if aseg_rna is None:
        return None
    return pd.read_csv(aseg_rna)


def parse_args():
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Visualize FreeSurfer aseg.nii file.")
    parser.add_argument(
        "--aseg_file",
        type=str,
        required=True,
        help="Path to the aseg.nii file.",
    )
    parser.add_argument(
        "--aseg_stats",
        type=str,
        required=True,
        help="Path to aseg.stats file.",
    )
    parser.add_argument("--aseg_rna", type=str, help="Path to ratio N/A file.")
    parser.add_argument(
        "--step_size",
        type=int,
        default=1,
        help="Step size for subsampling the data.",
    )
    parser.add_argument(
        "--opacity",
        type=float,
        default=0.7,
        help="Opacity of the mesh.",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        default=2.0,
        help="Smoothing factor (higher = smoother).",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output HTML file path.",
    )
    parser.add_argument(
        "--comparison",
        action="store_true",
        help="Create smoothing comparison visualization for hippocampus.",
    )
    parser.add_argument(
        "--comparison_structure",
        type=int,
        default=17,
        help="Structure ID to use for smoothing comparison (default: 17, Left-Hippocampus).",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    # Path to your aseg.nii file
    aseg_file = args.aseg_file

    # Use provided labels or default to subcortical structures
    aseg_stats = parse_aseg_stats(args.aseg_stats)
    aseg_rna = parse_aseg_rna(args.aseg_rna)

    # Create visualization
    fig = visualize_aseg(
        aseg_file,
        aseg_stats=aseg_stats,
        aseg_rna=aseg_rna,
        step_size=args.step_size,
        opacity=args.opacity,
        smoothing=args.smoothing,
    )

    # Show the figure
    fig.show()

    # Save HTML file
    if args.output:
        pio.write_html(fig, args.output)
        print(f"Visualization saved to {args.output}")

    # Create smoothing comparison if requested
    if args.comparison:
        print(
            f"Creating smoothing comparison for structure {args.comparison_structure}..."
        )
        comparison_fig = create_smoothing_comparison(
            aseg_file, structure_id=args.comparison_structure
        )
        comparison_fig.show()

        comparison_output = f"smoothing_comparison_{args.comparison_structure}.html"
        pio.write_html(comparison_fig, comparison_output)
        print(f"Comparison visualization saved to {comparison_output}")


# Example usage
if __name__ == "__main__":
    main()
