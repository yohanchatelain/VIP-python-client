import argparse
import glob
import os

import numpy as np
import pandas as pd
from numpy import dtype
import plotly.express as px
from significantdigits import significant_digits as sigdig


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


def compute_stats(lh, rh):
    stats_l = (
        lh.groupby("lh.aparc.a2009s.thickness")
        .agg(
            lambda x: sigdig(
                x.to_numpy().astype(np.float32),
                reference=np.mean(x).astype(dtype=np.float32),
                base=10,
            )
        )
        .transpose()
    )
    stats_r = (
        rh.groupby("rh.aparc.a2009s.thickness")
        .agg(
            lambda x: sigdig(
                x.to_numpy().astype(np.float32),
                reference=np.mean(x).astype(dtype=np.float32),
                base=10,
            )
        )
        .transpose()
    )
    stats = pd.concat((stats_l, stats_r))
    # print(stats)
    stats.drop(["BrainSegVolNotVent", "eTIV"], inplace=True)
    stats["hemi"] = stats.index.to_series().apply(lambda s: s.split("_")[0])
    stats.index = stats.index.to_series().apply(lambda s: "_".join(s.split("_")[1:]))
    return stats


def custom_mean(row):
    return pd.Series([np.mean(row[:-1]), row[-1]])


def plot(df):
    fig = px.box(
        df,
        x=df.index,
        y=df.columns,
        color="hemi",
    )
    fig.update_xaxes(title="Cortical Parcellation")
    fig.update_yaxes(title="Significant digits (mm)")
    fig.show()
    # df_pol = df.drop(columns=["hemi"])
    # mean = df.apply(custom_mean, axis=1)
    # mean.columns = pd.Index(["sig", "hemi"])
    # # print(mean)
    # fig = px.line_polar(mean, theta=mean.index, r=mean.sig, color="hemi")
    # fig.show()


def parse_args():
    parser = argparse.ArgumentParser("stats")
    parser.add_argument("--directory", default=".")
    parser.add_argument("--measure", help="Parse measure only")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    files_dict = get_files(args.directory, measure_to_parse=args.measure)
    df_dict = {}
    for (hemi, measure), files in files_dict.items():
        # print(hemi, measure)
        df = parse_file(files)
        # print(df)
        df_dict[measure] = df_dict.get(measure, {}) | {hemi: df}

    for measure, df_dict in df_dict.items():
        print(df_dict)
        stats = compute_stats(**df_dict)
        plot(stats)


if "__main__" == __name__:
    main()
