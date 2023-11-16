import argparse
import glob
import os
import sys
from typing import List
from warnings import simplefilter
import json

import numpy as np
import pandas as pd
from icecream import ic
from significantdigits import significant_digits as sigdig

from fsgd_parser import FSGDParser

ic.configureOutput(includeContext=True)

simplefilter(action="ignore", category=pd.errors.PerformanceWarning)


def end():
    sys.exit(0)


units = {
    "area": "",
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


def get_fsgd(filename: str) -> pd.DataFrame:
    parser = FSGDParser(filename, input_name="subjid", class_name="PD-status")
    parser.parse()
    return parser.as_dataframe()


def parse_file(filenames: List[str]) -> pd.DataFrame:
    df = pd.concat(pd.read_csv(f, sep="\t") for f in filenames)
    return df


def _get_basename_wo_ext(filename: str) -> str:
    """return basename filename without extension"""
    return os.path.splitext(os.path.basename(filename))[0]


def _get_files(files: List[str], columns: List[str]) -> pd.DataFrame:
    data = {file: _get_basename_wo_ext(file).split(".") for file in files}
    df = pd.DataFrame.from_dict(data, orient="index", columns=columns)
    return df


def get_files(directory: str, hemi: bool) -> pd.DataFrame:
    files = glob.glob(os.path.join(directory, "rep*.tsv"))
    ic(files)
    if hemi:
        columns = ["repetition", "hemi", "roi", "measure"]
    else:
        columns = ["repetition", "roi", "measure"]
    df = _get_files(files, columns=columns)
    return df


def compute_significantdigits(dtype, clip=True):
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


def make_df_hemi(df: pd.DataFrame, hemi: str) -> pd.DataFrame:
    """
    Preprocess hemi df
    """
    hemi_df = parse_file(df[df["hemi"] == hemi].index)
    hemi_prefixed_columns = [col for col in hemi_df.columns if col.startswith(hemi)]
    remove_prefix = {col: col[3:] for col in hemi_prefixed_columns}
    # other_columns = [col for col in hemi_df.columns if not col.startswith(hemi)]
    hemi_df.rename(columns=remove_prefix, inplace=True)
    hemi_df.rename(columns={hemi_df.columns[0]: "subjid"}, inplace=True)
    hemi_df["hemi"] = hemi
    return hemi_df


def make_df_area(
    df: pd.DataFrame, area: str = None, measure: str = None
) -> pd.DataFrame:
    df = parse_file(df.index)
    df.rename(columns={df.columns[0]: "subjid"}, inplace=True)
    return df


def make_df(
    df_files: pd.DataFrame, measure: str, hemi: bool, area: str = None
) -> pd.DataFrame:
    df = df_files[df_files["measure"] == measure]
    if hemi:
        lh = make_df_hemi(df, "lh")
        rh = make_df_hemi(df, "rh")
        df = pd.concat([lh, rh])
    else:
        df = make_df_area(df, area, measure)
    return df


def compute_stats_subject(
    df: pd.DataFrame, stats: str, hemi: bool, dtype: np.dtype = np.float64
) -> pd.DataFrame:
    id_vars = ["subjid"] + (["hemi"] if hemi else [])
    var_name = "ROI"
    value_name = "measure"

    if stats == "mean":
        df = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
        return df.groupby(id_vars + [var_name]).mean(numeric_only=True)
    if stats == "std":
        df = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
        return df.groupby(id_vars + [var_name]).std(numeric_only=True)
    if stats == "sig":
        df = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
        return df.groupby(id_vars + [var_name]).agg(compute_significantdigits(dtype))


def compute_stats_group(
    df: pd.DataFrame,
    fsgd: pd.DataFrame,
    stats: str,
    hemi: bool,
    dtype: np.dtype = np.float64,
) -> pd.DataFrame:
    df = pd.merge(left=df, right=fsgd).drop(columns=["age", "sex"])
    ic(df)

    id_vars = ["subjid", "PD-status"] + (["hemi"] if hemi else [])
    var_name = "ROI"
    value_name = "measure"

    if stats == "mean":
        df = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
        return df.groupby(id_vars + [var_name]).mean(numeric_only=True)
    if stats == "std":
        df = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
        return df.groupby(id_vars + [var_name]).std(numeric_only=True)
    if stats == "sig":
        df = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
        return df.groupby(id_vars + [var_name]).agg(compute_significantdigits(dtype))
    return df


def parse_args():
    parser = argparse.ArgumentParser("stats")
    parser.add_argument("--directory", default=".")
    parser.add_argument("--json-data", required=True, help="JSON data file")
    parser.add_argument(
        "--hemi",
        action="store_true",
        help="Hemisphere measurement (expect lh, rh prefixes)",
    )
    parser.add_argument("--measure", required=True, help="Parse measure only")
    parser.add_argument(
        "--fp-type",
        choices=list(fptypes.keys()),
        default=default_fptype,
        help="Input floating-point data type",
    )
    parser.add_argument(
        "--level-analysis",
        required=True,
        choices=["subject", "group"],
        help="Level analysis",
    )
    parser.add_argument("--fsgd", help="FSGD file")
    parser.add_argument("--output", default="output.csv", help="Output filename")
    parser.add_argument(
        "--stats-type",
        choices=["sig", "std", "mean", "none"],
        default="sig",
        help="Stats to measure",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    args = parser.parse_args()
    return args


def set_verbose_mode(verbose: bool):
    if verbose:
        ic.enable()
    else:
        ic.disable()


def drop_subjid_not_in_data(df: pd.DataFrame, json_data: str) -> pd.DataFrame:
    with open(json_data, "r") as f:
        data = json.load(f)
    return df[df.index.get_level_values("subjid").isin(data["PATNO_id"].values())]


def main():
    args = parse_args()
    set_verbose_mode(args.verbose)

    files_dict = get_files(args.directory, hemi=args.hemi)
    ic(files_dict)

    df = make_df(files_dict, args.measure, args.hemi)

    if args.level_analysis == "subject":
        stats = compute_stats_subject(
            df, stats=args.stats_type, hemi=args.hemi, dtype=args.fp_type
        )
    elif args.level_analysis == "group":
        fsgd = get_fsgd(args.fsgd)
        ic(fsgd)
        stats = compute_stats_group(
            df, fsgd=fsgd, stats=args.stats_type, hemi=args.hemi, dtype=args.fp_type
        )
    else:
        raise Exception("No level analysis provided")

    ic(stats)

    stats = drop_subjid_not_in_data(stats, args.json_data)
    ic(stats)

    stats.to_csv(args.output)


if "__main__" == __name__:
    main()
