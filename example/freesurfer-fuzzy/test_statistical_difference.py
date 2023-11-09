import argparse
from typing import List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from icecream import ic
from scipy.stats import mannwhitneyu


def qqplot(pvalues: List[float], title: str, output: str) -> None:
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


def test_statistical_difference(stats: pd.DataFrame, columns: List[str]) -> None:
    # Define the unique combinations of parcelation and hemi
    stats = stats.reset_index()
    ic(columns)
    unique_ROIs = stats[columns].drop_duplicates().values
    mann = []
    nb_ROIs = len(unique_ROIs)

    # Iterate through the unique combinations and apply the Mann-Whitney U test
    for ids in unique_ROIs:
        group = stats[stats[columns] == ids][columns]
        group = stats[group.notna().all(axis=1)]
        # Separate the values based on PD-Status
        group1 = group[group["PD-status"] == "PD-non-MCI"]["measure"]
        group2 = group[group["PD-status"] != "PD-non-MCI"]["measure"]

        # Apply the Mann-Whitney U test
        stat, p = mannwhitneyu(group1, group2)
        mann.append(p)
        if p < 0.05 / nb_ROIs:
            roi = ",".join(zip(columns, ids))
            print(f"[Mann-Whitney U  ] Statistics: {stat}, {roi}, p-value: {p}")

    return mann


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

    fig = qqplot(pvalues, args.title, args.output)

    if args.show:
        fig.show()


if "__main__" == __name__:
    main()
