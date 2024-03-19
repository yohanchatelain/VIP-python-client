import json
import argparse
import os

rootdir = os.path.dirname(os.path.abspath(__file__))
vip_outputs = os.path.realpath(os.path.join(rootdir, "../../../vip_outputs/"))
entropy_dir = os.path.realpath(os.path.join(rootdir, "../entropy/"))
entropy_json = os.path.realpath(os.path.join(rootdir, "../entropy.json"))
input_json = os.path.realpath(os.path.join(rootdir, "../../json/json_data.json"))


def read_json(filename):
    with open(filename, "r") as f:
        return json.load(f)


def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)


def generate_entropy_json(input_file, output_file, input_dir, output_dir):
    data = read_json(input_file)
    _json = [
        {
            "regexp": f"{input_dir}/rep*/{dataset}/mri/aparc.a2009s+aseg.mgz",
            "output": f"{output_dir}/{dataset}/entropy.nii.gz",
        }
        for dataset in data["PATNO_id"].values()
    ]
    return _json


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=input_json, type=str, help="Input json file")
    parser.add_argument(
        "--output", default=entropy_json, type=str, help="Output json file"
    )
    parser.add_argument(
        "--input-dir", default=vip_outputs, type=str, help="Input directory"
    )
    parser.add_argument(
        "--output-dir", default=entropy_dir, type=str, help="Output directory"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    data = generate_entropy_json(
        args.input, args.output, args.input_dir, args.output_dir
    )
    write_json(args.output, data)


if __name__ == "__main__":
    main()
