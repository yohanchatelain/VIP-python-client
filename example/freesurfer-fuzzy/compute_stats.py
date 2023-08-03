import argparse
import glob
import os
from warnings import simplefilter

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fsgd_parser import FSGDParser
from scipy.stats import mannwhitneyu, ttest_ind
from significantdigits import significant_digits as sigdig

simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

from icecream import ic

ic.configureOutput(includeContext=True)


units = {
    "curvind": "",
    "foldind": "",
    "gauscurv": "",
    "meancurv": "",
    "thicknessstd": "",
    "thickness": "",
    "volume": "",
}

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

default_fptype = "float64"
fptypes = {default_fptype: np.float64, "float32": np.float32, "float16": np.float16}


def get_fsgd(filename):
    parser = FSGDParser(filename, input_name="subjid", class_name="PD-status")
    parser.parse()
    return parser.as_dataframe()


def parse_file(filenames):
    df = pd.concat(pd.read_csv(f, sep="\t") for f in filenames)
    return df


def get_files(directory, measure_to_parse=None):
    files = glob.glob(os.path.join(directory, "rep*.tsv"))
    files_sorted = {}
    for file in files:
        (_, hemi, measure) = file.split("-")
        measure = os.path.splitext(measure)[0]
        key = (hemi, measure)
        if measure_to_parse is None or measure_to_parse == measure:
            files_sorted[key] = files_sorted.get(key, []) + [file]
    return files_sorted


def compute_sigdig(dtype, clip=True):
    def fun(x):
        y = sigdig(
            x.to_numpy().astype(np.float32),
            reference=np.mean(x).astype(dtype=np.float32),
            basis=10,
            dtype=dtype,
        )
        if clip:
            y = y.clip(0)
        return y

    return fun


def compute_stats(lh, rh, dtype):
    stats_name_l = lh.columns[0]
    stats_name_r = rh.columns[0]
    stats_l = lh.groupby(stats_name_l).agg(compute_sigdig(dtype)).transpose()
    stats_r = rh.groupby(stats_name_r).agg(compute_sigdig(dtype)).transpose()
    stats = pd.concat((stats_l, stats_r))
    stats.drop(["BrainSegVolNotVent", "eTIV"], inplace=True)
    stats["hemi"] = stats.index.to_series().apply(lambda s: s.split("_")[0])
    stats.index = stats.index.to_series().apply(lambda s: "_".join(s.split("_")[1:]))
    return stats


def preprocess_hemi_group(fsgd, hemi: pd.DataFrame):
    unique = hemi[hemi.columns[0]].value_counts() == 1
    unique = unique[unique]
    hemi = hemi[~hemi.isin(unique.index)]

    subjid = fsgd["subjid"]
    stats_name = hemi.columns[0]
    hemi = hemi[hemi[stats_name].isin(subjid)]

    hemi = pd.merge(left=hemi, right=fsgd, left_on=stats_name, right_on="subjid").drop(
        stats_name, axis=1
    )
    hemi.drop(["BrainSegVolNotVent", "eTIV", "age", "sex"], axis=1, inplace=True)
    hemi = pd.melt(
        hemi,
        id_vars=["subjid", "PD-status"],
        var_name="parcellation",
        value_name="thickness",
    )
    hemi["hemi"] = hemi["parcellation"].apply(lambda s: s.split("_")[0])
    hemi["parcellation"] = hemi["parcellation"].apply(
        lambda s: "_".join(s.split("_")[1:])
    )

    return hemi


def preprocess_volume_group(fsgd, volume: pd.DataFrame):
    unique = volume[volume.columns[0]].value_counts() == 1
    unique = unique[unique]
    volume = volume[~volume.isin(unique.index)]

    subjid = fsgd["subjid"]
    stats_name = volume.columns[0]
    volume = volume[volume[stats_name].isin(subjid)]

    volume = pd.merge(
        left=volume, right=fsgd, left_on=stats_name, right_on="subjid"
    ).drop(stats_name, axis=1)
    volume.drop(["age", "sex"], axis=1, inplace=True)
    volume = pd.melt(
        volume,
        id_vars=["subjid", "PD-status"],
        var_name="parcellation",
        value_name="thickness",
    )

    return volume


def qqplot(pvalues, title, output):
    x_identity = np.linspace(min(pvalues), max(pvalues), len(pvalues))
    y_identity = x_identity
    fig = px.scatter(x=x_identity, y=sorted(pvalues), trendline="ols")
    fig.add_trace(
        go.Scatter(x=x_identity, y=y_identity, mode="lines", line=dict(dash="dash"))
    )
    fig.update_yaxes(title="p-values")
    fig.update_layout(title=title)
    fig.write_html(f"qqplot-{output}.html")
    fig.write_image(f"qqplot-{output}.png")


def test_statistical_difference_hemi(stats):
    # Define the unique combinations of parcelation and hemi
    unique_combinations = stats[["parcellation", "hemi"]].drop_duplicates().values

    ttest = []
    mann = []
    parcellations = len(unique_combinations)

    # Iterate through the unique combinations and apply the Mann-Whitney U test
    for parcellation, hemi in unique_combinations:
        group = stats[(stats["parcellation"] == parcellation) & (stats["hemi"] == hemi)]

        # Separate the values based on PD-Status
        group1 = group[group["PD-status"] == "PD-non-MCI"]["thickness"]
        group2 = group[group["PD-status"] != "PD-non-MCI"]["thickness"]

        # Apply the Mann-Whitney U test
        stat, p = mannwhitneyu(group1, group2)
        mann.append(p)
        if p < 0.05 / parcellations:
            print(
                f"[Mann-Whitney U  ] Parcelation: {parcellation}, Hemisphere: {hemi}, Statistics: {stat}, p-value: {p/parcellations}"
            )

        # Apply the Student's t-test test
        stat, p = ttest_ind(group1, group2)
        ttest.append(p)
        if p < 0.05 / parcellations:
            print(
                f"[Student's t-test] Parcelation: {parcellation}, Hemisphere: {hemi}, Statistics: {stat}, p-value: {p/parcellations}"
            )

    qqplot(mann, "Mann-Whitney U test", "mann-whitney-hemi")
    qqplot(ttest, "Student's t-test", "ttest-hemi")


def test_statistical_difference(stats):
    # Define the unique combinations of parcelation and hemi
    unique_combinations = stats[["parcellation"]].drop_duplicates().values

    mann = []
    ttest = []

    parcellations = len(unique_combinations)
    # Iterate through the unique combinations and apply the Mann-Whitney U test
    for parcellation in unique_combinations:
        group = stats[stats["parcellation"] == parcellation[0]]

        # Separate the values based on PD-Status
        group1 = group[group["PD-status"] == "PD-non-MCI"]["thickness"]
        group2 = group[group["PD-status"] != "PD-non-MCI"]["thickness"]

        # Apply the Mann-Whitney U test
        stat, p = mannwhitneyu(group1, group2)
        mann.append(p)
        if p < 0.05 / parcellations:
            print(
                f"[Mann-Whitney U  ] Parcelation: {parcellation},  Statistics: {stat}, p-value: {p/parcellations}"
            )

        # Apply the Student's t-test test
        stat, p = ttest_ind(group1, group2)
        ttest.append(p)
        if p < 0.05 / parcellations:
            print(
                f"[Student's t-test] Parcelation: {parcellation},  Statistics: {stat}, p-value: {p/parcellations}"
            )

    qqplot(mann, "Mann-Whitney U test", "mann-whitney-volume")
    qqplot(ttest, "Student's t-test", "ttest-volume")


def compute_stats_group(
    lh: pd.DataFrame, rh: pd.DataFrame, dtype: np.dtype, fsgd: pd.DataFrame
):
    fsgd["age"] = pd.to_numeric(fsgd["age"])

    lh = preprocess_hemi_group(fsgd, lh)
    rh = preprocess_hemi_group(fsgd, rh)

    stats = pd.concat([lh, rh])

    stats = stats.groupby(["subjid", "parcellation", "hemi", "PD-status"])[
        ["thickness"]
    ].agg(compute_sigdig(dtype))
    stats.reset_index(inplace=True)

    test_statistical_difference_hemi(stats)

    return stats


def compute_stats_volume(lh, rh, cortical, dtype):
    hemi_stats = compute_stats(lh, rh, dtype)
    stats_name = cortical.columns[0]
    volume_stats = cortical.groupby(stats_name).agg(compute_sigdig(dtype))
    return hemi_stats, volume_stats


def compute_stats_volume_group(lh, rh, cortical, dtype, fsgd):
    hemi_stats = compute_stats_group(lh, rh, dtype, fsgd)
    volume = preprocess_volume_group(fsgd, cortical)

    fsgd["age"] = pd.to_numeric(fsgd["age"])

    volume_stats = volume.groupby(["subjid", "parcellation", "PD-status"])[
        ["thickness"]
    ].agg(compute_sigdig(dtype))
    volume_stats.reset_index(inplace=True)

    test_statistical_difference_hemi(hemi_stats)
    test_statistical_difference(volume_stats)

    return hemi_stats, volume_stats


def plot_hemi(df, title, show):
    fig = px.box(
        df,
        x=df.index,
        y=df.columns,
        color="hemi",
    )
    fig.update_layout(title=title)
    fig.update_xaxes(title="Cortical Parcellation")
    fig.update_yaxes(title="Significant digits (mm)")
    if show:
        fig.show()
    fig.write_html(f"{title}.html")
    fig.write_image(f"{title}.png")


def plot_hemi_group(df, title, show):
    fig = px.box(
        df,
        x="parcellation",
        y="thickness",
        color="hemi",
        facet_row="PD-status",
    )
    fig.update_layout(title=title)
    fig.update_xaxes(title="Cortical Parcellation")
    fig.update_yaxes(title="Significant digits (mm)")
    if show:
        fig.show()
    fig.write_html(title)
    fig.write_image(title, format="png")


def plot_cortical_volume(df, title, show):
    df.drop(columns=volume_units["unitless"], inplace=True)
    fig = px.box(df, y=df.columns)
    fig.update_layout(title=title)
    fig.update_xaxes(title="Cortical Parcellation")
    fig.update_yaxes(title="Volume (mm^3)")
    if show:
        fig.show()
    fig.write_html(f"{title}.html")
    fig.write_image(f"{title}.png")


def plot_cortical_volume_group(df, title, show):
    fig = px.box(df, x="parcellation", y="thickness", facet_col="PD-status")
    fig.update_layout(title=title)
    fig.update_xaxes(title="Cortical Parcellation")
    fig.update_yaxes(title="Volume (mm^3)")
    if show:
        fig.show()
    fig.write_html(f"{title}-group.html")
    fig.write_image(f"{title}-group.png")


def make_df(files_dict):
    df_dict = {}
    for (hemi, measure), files in files_dict.items():
        df = parse_file(files)
        df_dict[measure] = df_dict.get(measure, {}) | {hemi: df}
    return df_dict


def plot_subject(args, df):
    for measure, df_dict in df.items():
        df_dict["dtype"] = fptypes[args.fp_type]

        if "cortical" in df_dict:
            hemi_stats, volume_stats = compute_stats_volume(**df_dict)
            plot_hemi(hemi_stats, title=measure, show=args.show)
            plot_cortical_volume(volume_stats, title=measure, show=args.show)
        else:
            hemi_stats = compute_stats(**df_dict)
            plot_hemi(hemi_stats, title=measure, show=args.show)


def plot_group(args, df):
    fsgd = get_fsgd(args.fsgd)
    for measure, df_dict in df.items():
        df_dict["dtype"] = fptypes[args.fp_type]
        df_dict["fsgd"] = fsgd
        if "cortical" in df_dict:
            hemi_stats, volume_stats = compute_stats_volume_group(**df_dict)
            plot_hemi_group(hemi_stats, title=measure, show=args.show)
            plot_cortical_volume_group(volume_stats, title=measure, show=args.show)
        else:
            hemi_stats = compute_stats_group(**df_dict)
            plot_hemi_group(hemi_stats, title=measure, show=args.show)


def parse_args():
    parser = argparse.ArgumentParser("stats")
    parser.add_argument("--directory", default=".")
    parser.add_argument("--measure", help="Parse measure only")
    parser.add_argument(
        "--fp-type",
        choices=list(fptypes.keys()),
        default=default_fptype,
        help="Input floating-point data type",
    )
    parser.add_argument("--show", action="store_true", help="Show figures")
    parser.add_argument("--fsgd", help="FSGD file")
    parser.add_argument(
        "--plot-subject", action="store_true", help="Plot subject analysis"
    )
    parser.add_argument("--plot-group", action="store_true", help="Plot group analysis")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    files_dict = get_files(args.directory, measure_to_parse=args.measure)
    df_dict = make_df(files_dict)

    if args.plot_subject:
        plot_subject(args, df_dict)

    if args.plot_group:
        plot_group(args, df_dict)


if "__main__" == __name__:
    main()
