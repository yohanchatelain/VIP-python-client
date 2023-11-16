import argparse
from typing import List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objects import Figure
from icecream import ic
from scipy.stats import ttest_ind_from_stats
from scipy.stats import combine_pvalues


def qqplot(pvalues: List[float], title: str, output: str) -> Figure:
    x_identity = np.linspace(min(pvalues), max(pvalues), len(pvalues))
    y_identity = x_identity
    fig = px.scatter(x=x_identity, y=sorted(pvalues), trendline="ols")
    fig.add_trace(
        go.Scatter(
            x=x_identity,
            y=y_identity,
            mode="lines",
            line=dict(dash="dash"),
            name="identity",
        )
    )
    fig.update_xaxes(title="Index")
    fig.update_yaxes(title="p-values")
    fig.update_layout(title=title)

    fig.write_html(f"{output}.html")
    fig.write_image(f"{output}.png", width=1920, height=1080)

    return fig


def test_statistical_difference(stats: pd.DataFrame, columns: List[str]) -> List[float]:
    # Define the unique combinations of parcelation and hemi
    stats = stats.reset_index()
    ic(columns)
    unique_rois = stats[columns].drop_duplicates().values
    pvalues = []
    nb_rois = len(unique_rois)

    # Iterate through the unique combinations and apply the Mann-Whitney U test
    for ids in unique_rois:
        group = stats[stats[columns] == ids][columns]
        group = stats[group.notna().all(axis=1)]
        # Separate the values based on PD-Status
        group1 = group[group["PD-status"] == "PD-non-MCI"]["measure"]
        group2 = group[group["PD-status"] != "PD-non-MCI"]["measure"]

        # Apply the T-test
        mean1 = group1.mean()
        std1 = group1.std()
        nobs1 = group1.count()
        mean2 = group2.mean()
        std2 = group2.std()
        nobs2 = group2.count()

        stat, p = ttest_ind_from_stats(
            mean1=mean1, std1=std1, mean2=mean2, std2=std2, nobs1=nobs1, nobs2=nobs2
        )

        if np.isnan(p):
            print(f"NaN p-value: {p} for {ids}")
            print(mean1, std1, nobs1)
            print(mean2, std2, nobs2)
        else:
            pvalues.append(p)

        if p < 0.05 / nb_rois:
            roi = ",".join(zip(columns, ids))
            print(f"T-test] Statistics: {stat}, {roi}, p-value: {p}")

    return pvalues


def fisher_method(pvalues):
    methods = [
        # "fisher",
        "pearson",
        # "stouffer",
        # "mudholkar_george",
        # "tippett",
    ]
    for method in methods:
        stats, pvalue = combine_pvalues(pvalues, method=method)
        if pvalue < 0.05:
            print(f"Fisher's method ({method}): {pvalue}")


def parse_filename(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename)
    return df


def parse_args():
    parser = argparse.ArgumentParser("test-stat-diff")
    parser.add_argument("--filename", help="Inputs CSV filename")
    parser.add_argument("--show", action="store_true", help="Show figure")
    parser.add_argument("--output", help="Output filename")
    parser.add_argument("--title", default="Mann-Whitney U test", help="Figure's title")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    df = parse_filename(args.filename)

    if "PD-status" not in df.columns:
        raise Exception("No PD-status column found")

    columns = ["ROI"] + (["hemi"] if "hemi" in df.columns else [])
    pvalues = test_statistical_difference(df, columns)
    fisher_method(pvalues)

    fig = qqplot(pvalues, args.title, args.output)

    if args.show:
        fig.show()


if "__main__" == __name__:
    main()
