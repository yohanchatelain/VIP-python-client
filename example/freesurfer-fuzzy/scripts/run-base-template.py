import argparse
import json
import os
import subprocess
import tarfile
import time
import traceback
from functools import wraps

import pytainer
from joblib import Parallel, delayed

DRY_RUN_ENABLED = False

DST_LICENSE_DIR = "/etc/license"
DST_LICENSE_PATH = os.path.join("license.txt")
DST_HOME_DIR = "/home/"
DST_SUBJECTS_DIR = DST_HOME_DIR


class ArgumentScript:
    def __init__(
        self,
        fs_image,
        options,
        first_visit,
        second_visit,
        base_template,
        archive_dir,
        output_dir,
    ):
        self.fs_image = fs_image
        self.options = options
        self.first_visit = first_visit
        self.second_visit = second_visit
        self.base_template = base_template
        self.archive_dir = archive_dir
        self.output_dir = output_dir

    def to_list(self):
        return [
            self.fs_image,
            self.options,
            self.first_visit,
            self.second_visit,
            self.base_template,
        ]


def dry_run_decorator(force_call=False):
    """
    Decorator to enable dry run mode for a function.
    If 'dry_run' parameter is True, the function will only log its actions instead of performing them.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if DRY_RUN_ENABLED:
                print(f"== [{func.__name__}] call start == ")
                print(f"\targs={args}, kwargs={kwargs}")
                print(f"== [{func.__name__}] call end == ")
                return None if not force_call else func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


@dry_run_decorator(force_call=True)
def close_to_quota_limit(username="ychatel", ratio_limit=0.95):
    # Call the quota command to check the scratch quota
    # returns output like:
    #                        Description                Space           # of files
    #          /scratch (project ychatel)            2323M/20T            52k/1000k
    #
    # Disk usage can be explored using the following commands:
    # diskusage_explorer /scratch/ychatel        (Last update: 2023-11-21 12:08:49)
    def expand_units(value):
        return value.replace("k", "000")

    try:
        result = subprocess.run(
            ["diskusage_report", "--scratch"], check=True, capture_output=True
        )
    except subprocess.CalledProcessError as e:
        raise e
    stdout = result.stdout.decode().split("\n")
    for line in stdout:
        if f"project {username}" in line:
            quota = line.split()[-1]
            [current, limit] = quota.split("/")
            current = int(expand_units(current))
            limit = int(expand_units(limit))
            if current / limit > ratio_limit:
                return True
            return False


@dry_run_decorator()
def dump_output(args, result):
    os.makedirs(os.path.join(args.output_dir, "log"), exist_ok=True)
    stdout_log_filename = (
        f"stdout-{args.first_visit}_{args.second_visit}_{args.base_template}.txt"
    )
    stderr_log_filename = (
        f"stderr-{args.first_visit}_{args.second_visit}_{args.base_template}.txt"
    )
    stdout_log = os.path.join(args.output_dir, "log", stdout_log_filename)
    stderr_log = os.path.join(args.output_dir, "log", stderr_log_filename)
    stdout = result.stdout
    stderr = result.stderr
    with open(stdout_log, "w") as fo:
        fo.write(stdout)
    with open(stderr_log, "w") as fo:
        fo.write(stderr)


@dry_run_decorator(force_call=True)
def create_fixed_options(
    src_license_dir,
    dst_license_dir,
    src_home,
    dst_home,
    dst_subjects_dir,
    dst_license_path,
):
    options = pytainer.PytainerOptionsExec()
    options.bind(src_license_dir, dst_license_dir)
    options.bind(src_home, dst_home)
    options.env("SUBJECTS_DIR", dst_subjects_dir)
    options.env("FS_LICENSE", dst_license_path)
    return options


@dry_run_decorator()
def extract_if_not_exists(visit, src, dst):
    extracted_visit_abspath = os.path.join(src, visit)
    if not os.path.exists(extracted_visit_abspath):
        tar_visit_abspath = os.path.join(src, visit + ".tgz")
        if os.path.exists(tar_visit_abspath):
            with tarfile.open(tar_visit_abspath) as tar:
                tar.extractall(dst)
        else:
            raise RuntimeError(f"Cannot find the visit {visit}: {tar_visit_abspath}")


@dry_run_decorator()
def zip(src, dst):
    try:
        with tarfile.open(dst, "w:gz") as tar:
            tar.add(src, arcname=os.path.basename(src))
    except Exception as e:
        return False
    return True


@dry_run_decorator()
def run_fs_base_template_apptainer(args: ArgumentScript) -> None:
    pytnr = pytainer.Pytainer(args.fs_image)
    base_template = f"-base {args.base_template}"
    first_visit = f"-tp {args.first_visit}"
    second_visit = f"-tp {args.second_visit}"
    command = ["recon-all", base_template, first_visit, second_visit, "-all"]
    result = pytnr.exec(command, args.options)
    if result.has_failed():
        raise RuntimeError(result.command_flatten, result.stderr)
    dump_output(args, result)


@dry_run_decorator(force_call=True)
def make_args(
    fs_image, options, first_visit, second_visit, base_template, archive_dir, output_dir
):
    args = []
    for patno in first_visit.keys():
        visit1 = first_visit[patno]
        visit2 = second_visit[patno]
        base = base_template[patno]
        arg = ArgumentScript(
            fs_image=fs_image,
            options=options,
            first_visit=visit1,
            second_visit=visit2,
            base_template=base,
            archive_dir=archive_dir,
            output_dir=output_dir,
        )
        args.append(arg)

    return args


@dry_run_decorator()
def remove(file):
    os.remove(file)


@dry_run_decorator()
def mkdirs(path, exist_ok=True):
    os.makedirs(path, exist_ok=exist_ok)


@dry_run_decorator(force_call=True)
def preprocess(args: ArgumentScript):
    while close_to_quota_limit():
        print("Waiting for the quota to be available")
        time.sleep(60)
    extract_if_not_exists(args.first_visit, args.archive_dir, args.output_dir)
    extract_if_not_exists(args.second_visit, args.archive_dir, args.output_dir)
    mkdirs("base_template", exist_ok=True)


@dry_run_decorator(force_call=True)
def postprocess(args: ArgumentScript):
    archive_output_path = os.path.join(args.archive_dir, args.base_template + ".tar.gz")
    if zip(args.base_template, archive_output_path):
        remove(args.base_template)
    else:
        print("Failed to zip the base template: ", args.base_template)


@dry_run_decorator(force_call=True)
def run_script(args: ArgumentScript):
    try:
        preprocess(args)
        run_fs_base_template_apptainer(args)
        postprocess(args)
    except RuntimeError as e:
        command = e.args[0]
        stderr = e.args[1]
        msg = f"RuntimeError occurred while running the script:\n{command}\n{stderr}"
        return msg
    except Exception as e:
        error_traceback = traceback.format_exc()
        msg = f"Error occurred while running the script:\n{e}\n{error_traceback}"
        return msg


def parse_args():
    parser = argparse.ArgumentParser("run-base-template")
    parser.add_argument(
        "--fs-image", required=True, help="Freesurfer image apptainer image path"
    )
    parser.add_argument("--input", default="json_data_base.json")
    parser.add_argument(
        "--repetition",
        required=True,
        type=int,
        help="Repetition number of the experiment",
    )
    parser.add_argument(
        "--archive-dir",
        required=True,
        help="Archive directory that contains the .tar.gz subject files",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory that contains the subject directory",
    )
    parser.add_argument(
        "--src-license-dir", required=True, help="License directory in host"
    )
    parser.add_argument("--src-home", required=True, help="Home directory in host")
    parser.add_argument(
        "--dst-license-dir", default=DST_LICENSE_DIR, help="License dir in container"
    )
    parser.add_argument(
        "--dst-home", default=DST_HOME_DIR, help="Home directory in container"
    )
    parser.add_argument(
        "--dst-subjects-dir", default=DST_SUBJECTS_DIR, help="Subjects dir in container"
    )
    parser.add_argument(
        "--dst-license-path", default=DST_LICENSE_PATH, help="License path in container"
    )
    parser.add_argument("--dry-run", action="store_true", help="Enable dry run mode")
    parser.add_argument("--n-jobs", type=int, default=-1)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    global DRY_RUN_ENABLED
    DRY_RUN_ENABLED = args.dry_run

    with open(args.input) as fi:
        maps = json.load(fi)

    src_license_dir = args.src_license_dir
    dst_license_dir = args.dst_license_dir
    src_home = args.src_home
    dst_home = args.dst_home
    dst_subjects_dir = args.dst_subjects_dir
    dst_license_path = args.dst_license_path

    options = create_fixed_options(
        src_license_dir,
        dst_license_dir,
        src_home,
        dst_home,
        dst_subjects_dir,
        dst_license_path,
    )

    first_visit = maps["first_visit"]
    second_visit = maps["second_visit"]
    base_template = maps["PATNO_base"]

    script_args = make_args(
        fs_image=args.fs_image,
        options=options,
        first_visit=first_visit,
        second_visit=second_visit,
        base_template=base_template,
        archive_dir=args.archive_dir,
        output_dir=args.output_dir,
    )

    n_jobs = max(args.n_jobs, len(script_args)) if args.n_jobs != -1 else -1
    results = Parallel(n_jobs=n_jobs)(delayed(run_script)(arg) for arg in script_args)

    for i, result in enumerate(results or []):
        if result:
            print(f"Result {i}:\n{result}")


if __name__ == "__main__":
    main()
