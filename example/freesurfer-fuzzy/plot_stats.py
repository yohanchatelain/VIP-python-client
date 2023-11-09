import plotly.express as px
import argparse
import pandas as pd
import sys
from warnings import simplefilter

simplefilter(action="ignore", category=DeprecationWarning)


# ROI to excludes
# cortical: BrainSegVolNotVent, eTIV
# subcortical: any ROI not starting with Left- or Right-
def filter_roi(df, region):
    if region == "cortical":
        df["ROI"] = df["ROI"][~df["ROI"].isin(["BrainSegVolNotVent", "eTIV"])]
    if region == "subcortical":
        df["ROI"] = df["ROI"][
            df["ROI"].str.startswith("Left-") | df["ROI"].str.startswith("Right-")
        ]
    return df


volume_units = {
    "mm3": [
        "Left-Lateral-Ventricle",
        "Left-Inf-Lat-Vent",
        "Left-Cerebellum-White-Matter",
        "Left-Cerebellum-Cortex",
        "Left-Thalamus",
        "Left-Caudate",
        "Left-Putamen",
        "Left-Pallidum",
        "3rd-Ventricle",
        "4th-Ventricle",
        "Brain-Stem",
        "Left-Hippocampus",
        "Left-Amygdala",
        "CSF",
        "Left-Accumbens-area",
        "Left-VentralDC",
        "Left-vessel",
        "Left-choroid-plexus",
        "Right-Lateral-Ventricle",
        "Right-Inf-Lat-Vent",
        "Right-Cerebellum-White-Matter",
        "Right-Cerebellum-Cortex",
        "Right-Thalamus",
        "Right-Caudate",
        "Right-Putamen",
        "Right-Pallidum",
        "Right-Hippocampus",
        "Right-Amygdala",
        "Right-Accumbens-area",
        "Right-VentralDC",
        "Right-vessel",
        "Right-choroid-plexus",
        "5th-Ventricle",
        "WM-hypointensities",
        "Left-WM-hypointensities",
        "Right-WM-hypointensities",
        "non-WM-hypointensities",
        "Left-non-WM-hypointensities",
        "Right-non-WM-hypointensities",
        "Optic-Chiasm",
        "CC_Posterior",
        "CC_Mid_Posterior",
        "CC_Central",
        "CC_Mid_Anterior",
        "CC_Anterior",
    ],
    "mm3-whole": [
        "BrainSegVol",
        "BrainSegVolNotVent",
        "VentricleChoroidVol",
        "lhCortexVol",
        "rhCortexVol",
        "CortexVol",
        "lhCerebralWhiteMatterVol",
        "rhCerebralWhiteMatterVol",
        "CerebralWhiteMatterVol",
        "SubCortGrayVol",
        "TotalGrayVol",
        "SupraTentorialVol",
        "SupraTentorialVolNotVent",
        "MaskVol",
        "EstimatedTotalIntraCranialVol",
    ],
    "unitless": [
        "BrainSegVol-to-eTIV",
        "MaskVol-to-eTIV",
        "lhSurfaceHoles",
        "rhSurfaceHoles",
        "SurfaceHoles",
    ],
}


def plot_box(
    df,
    x,
    y,
    title,
    show,
    output,
    log_y,
    xaxis,
    yaxis,
    facet_row=None,
    facet_col=None,
    color=None,
    color_discrete_sequence=None,
):
    fig = px.box(
        df,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=color_discrete_sequence,
        facet_row=facet_row,
        facet_col=facet_col,
        log_y=log_y,
    )
    fig.update_layout(title=title)
    fig.update_xaxes(title=xaxis)
    fig.update_yaxes(title=yaxis)

    fig.write_html(f"{output}.html")
    fig.write_image(f"{output}.png", width=1920, height=1080)

    if show:
        fig.show()


def plot_subject_level(df, title, show, output, color, log_y, xaxis, yaxis, facet_col):
    # subject level
    # color: hemi | None
    # facet_col: FS vs MCA | None
    plot_box(
        df,
        x="ROI",
        y="measure",
        color=color,
        color_discrete_sequence=["#f37736", "#7bc043"],
        show=show,
        output=output,
        log_y=log_y,
        facet_col=facet_col,
        title=title,
        xaxis=xaxis,
        yaxis=yaxis,
    )


def plot_group_level(
    df, title, show, output, log_y, xaxis, yaxis, facet_row, facet_col
):
    # group level
    # color: PD-status
    # facet_row: hemi | None
    # facet_col:? FS vs MCA | None
    plot_box(
        df,
        x="ROI",
        y="measure",
        color="PD-status",
        color_discrete_sequence=["#ee4035", "#0392cf"],
        log_y=log_y,
        facet_row=facet_row,
        facet_col=facet_col,
        title=title,
        xaxis=xaxis,
        yaxis=yaxis,
        show=show,
        output=output,
    )


def parse_csv(filename):
    df = pd.read_csv(filename)
    return df


def get_dataframe(args):
    df_mca = parse_csv(args.mca_filename) if args.mca_filename else pd.DataFrame()
    df_version = (
        parse_csv(args.version_filename) if args.version_filename else pd.DataFrame()
    )

    if not df_mca.empty:
        df_mca["comparison-mode"] = "mca"
    if not df_version.empty:
        df_version["comparison-mode"] = "version"

    return pd.concat((df_mca, df_version))


def parse_args():
    parser = argparse.ArgumentParser("stats")
    parser.add_argument("--version-filename", help="Between versions file name")
    parser.add_argument("--mca-filename", help="Within version file name")
    parser.add_argument("--analysis-level", choices=["subject", "group"], required=True)
    parser.add_argument("--show", action="store_true", help="Show figures")
    parser.add_argument("--xaxis", help="X-axis label")
    parser.add_argument("--yaxis", help="Y-axis label")
    parser.add_argument("--log-yaxis", action="store_true", help="Y-axis log")
    parser.add_argument("--title", help="Figure title")
    parser.add_argument("--output", required=True, help="Output filename")
    parser.add_argument(
        "--region",
        required=True,
        choices=["cortical", "subcortical"],
        help="Region to plot",
    )
    args = parser.parse_args()
    return args


def get_color(df):
    return "hemi" if "hemi" in df.columns else None


def main():
    args = parse_args()

    df = get_dataframe(args)

    if df.empty:
        print("No filenames provided")
        sys.exit(0)

    df = filter_roi(df, args.region)

    if args.analysis_level == "subject":
        color = "hemi" if "hemi" in df.columns else None
        facet_col = (
            "comparison-mode"
            if df["comparison-mode"].isin({"mca", "version"}).all()
            else None
        )
        plot_subject_level(
            df,
            title=args.title,
            show=args.show,
            output=args.output,
            color=color,
            log_y=args.log_yaxis,
            xaxis=args.xaxis,
            yaxis=args.yaxis,
            facet_col=facet_col,
        )

    elif args.analysis_level == "group":
        facet_col = (
            "comparison-mode"
            if df["comparison-mode"].isin({"mca", "version"}).all()
            else None
        )
        facet_row = "hemi" if "hemi" in df.columns else None
        plot_group_level(
            df,
            title=args.title,
            show=args.show,
            output=args.output,
            log_y=args.log_yaxis,
            xaxis=args.xaxis,
            yaxis=args.yaxis,
            facet_col=facet_col,
            facet_row=facet_row,
        )


if "__main__" == __name__:
    main()
