import abc
import argparse
import glob
import json
import os
import sys
from functools import partial

import cupy as cp
import cupyx as cpx
import joblib
import nibabel
import numpy as np
import tqdm
from icecream import ic
from joblib import Parallel, delayed

ic.configureOutput(includeContext=True)


class PBar:
    def __init__(self, total, desc, unit, verbose, position=0, postfix=None):
        self.total = total
        self.desc = desc
        self.unit = unit
        self.postfix = postfix
        self.verbose = verbose
        self.position = position
        if self.verbose:
            self.pbar = tqdm.tqdm(
                total=total, desc=desc, unit=unit, postfix=postfix, position=position
            )

    def update(self):
        if self.verbose:
            self.pbar.update()


# abstract class
class IOHandler(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def load(path):
        pass

    @staticmethod
    @abc.abstractmethod
    def save(data, path):
        pass

    @staticmethod
    def rename_output_kfold(output, i):
        return (
            os.path.dirname(output) + os.path.sep + f"{i}_" + os.path.basename(output)
        )


class IOHandlerNibabel(IOHandler):

    @staticmethod
    def load(path):
        ic(path)
        return nibabel.load(path).get_fdata()

    @staticmethod
    def save(data, path):
        ic(path)
        nibabel.save(
            nibabel.Nifti1Image(data, np.eye(4)),
            path,
        )


def safe_loader(segmentation, loader, dtype):
    """
    Load a segmentation file and cast it to a given dtype
    Raises a TypeError if the segmentation labels exceed the maximum value of the dtype
    """
    try:
        return loader(segmentation).astype(dtype, casting="safe").ravel()
    except TypeError:
        data = loader(segmentation)
        _max = np.iinfo(dtype).max
        _max_data = np.max(data)
        if _max_data <= _max:
            return data.astype(dtype).ravel()
        else:
            _name = np.iinfo(dtype).dtype.name
            error = (
                f"Maximum segmentation label value ({_max_data}) exceed maximum value ({_max}) of {_name}\n"
                "Increase the dtype size with --dtype"
            )
        print(error, file=sys.stderr)
        sys.exit(1)


class Segmentations:

    def __init__(self, iohandler, regexp, dtype, ncpus, verbose):
        self._files = None
        self._regexp = regexp
        self._iohandler = iohandler
        self._ncpus = ncpus
        self._dtype = dtype
        self._verbose = verbose
        self._shape = None
        self._sample_size = None
        self._segmentations = None
        self._labels = None

    @property
    def verbose(self):
        return self._verbose

    @property
    def shape(self):
        if self._shape is None:
            self._shape = self._iohandler.load(self.files[0]).shape
        return self._shape

    @property
    def sample_size(self):
        if self._sample_size is None:
            self._sample_size = len(self.files)
        return self._sample_size

    @property
    def labels(self):
        if self._labels is None:
            with cp.cuda.Device():
                segmentations_gpu = cp.asarray(self.segmentations)
                self._labels = cp.unique(segmentations_gpu).get()
        ic(self._labels)
        return self._labels

    def get_labels(self, segmentations_gpu):
        return cp.unique(segmentations_gpu).get()

    @property
    def files(self):
        if self._files is None:
            self._files = glob.glob(self._regexp)
            if len(self._files) == 0:
                raise FileNotFoundError("No segmentations found")
        self._sample_size = len(self._files)
        return self._files

    def _load_segmentations(self):
        safe_loader_fun = partial(
            safe_loader, loader=self._iohandler.load, dtype=self._dtype
        )
        with Parallel(
            n_jobs=self._ncpus, verbose=(1 if self._verbose else 0)
        ) as parallel:
            _segmentations = parallel(
                delayed(safe_loader_fun)(seg) for seg in self.files
            )
            self._segmentations = np.fromiter(
                _segmentations,
                dtype=np.dtype((self._dtype, np.prod(self.shape))),
            )

    @property
    def segmentations(self):
        if self._segmentations is None:
            self._load_segmentations()
        return self._segmentations


class KFoldEntropy:

    def __init__(self, segmentations: Segmentations, ngpus: int):
        self._segmentations = segmentations
        self._ngpus = ngpus
        self._chunks = self._get_chunks()
        self._current = 0
        ic(self._ngpus)
        ic(self._chunks)

    @property
    def ngpus(self):
        return self._ngpus

    def _get_chunks(self):
        if self._segmentations is None:
            raise ValueError("Segmentations not loaded")
        return np.array_split(np.arange(self._segmentations.sample_size), self._ngpus)

    def __iter__(self):
        return self

    def __next__(self):
        if self._current >= len(self._chunks):
            raise StopIteration
        result = self._chunks[self._current]
        self._current += 1
        return result


def compute_entropy_kernel_kfold(
    segmentations: Segmentations, iohandler: IOHandler, output: str, chunks, gpuid: int
):
    """
    Compute entropy for a kfold chunk
    """
    shape = segmentations.shape
    sample_size = segmentations.sample_size
    with cp.cuda.Device(gpuid):
        segmentations_gpu = cp.asarray(segmentations.segmentations)
        _index = cp.arange(sample_size, dtype=np.uint32)
        entropy = cp.zeros(np.prod(shape), dtype=np.float32)
        for i in chunks:
            pbar = PBar(
                total=segmentations.labels.size,
                desc=f"({gpuid}) [{i:02}/{chunks[-1]:02}] Computing entropy",
                unit="label",
                position=gpuid,
                verbose=segmentations.verbose,
            )
            for label in segmentations.get_labels(segmentations_gpu):
                p = cp.mean(
                    segmentations_gpu[_index != i, :] == label, dtype=np.float32, axis=0
                )
                entropy += cp.nan_to_num(p * cp.log2(p), nan=0, posinf=0, neginf=0)
                pbar.update()
            output_i = iohandler.rename_output_kfold(output, i)
            iohandler.save(entropy.get().reshape(shape), output_i)
            entropy.fill(0)


def compute_entropy_kernel_global(
    segmentations: Segmentations, iohandler: IOHandler, output: str
):
    """
    Compute entropy for the entire sample
    """
    shape = segmentations.shape
    ic(shape)
    with cp.cuda.Device():
        segmentations_gpu = cp.asarray(segmentations.segmentations)
        entropy = cp.zeros(np.prod(shape), dtype=cp.float32)
        pbar = PBar(
            total=segmentations.labels.size,
            desc="Computing entropy",
            unit="label",
            verbose=segmentations.verbose,
        )
        for label in segmentations.get_labels(segmentations_gpu):
            p = cp.mean(segmentations_gpu == label, dtype=cp.float32, axis=0)
            entropy += cp.nan_to_num(p * cp.log2(p), nan=0, posinf=0, neginf=0)
            pbar.update()
        iohandler.save(entropy.get().reshape(shape), output)


def compute_entropy(
    segmentations: Segmentations,
    kf: KFoldEntropy | None,
    iohandler: IOHandler,
    output: str,
):

    if kf is None:
        compute_entropy_kernel_global(segmentations, iohandler, output)
    elif kf.ngpus == 1:
        compute_entropy_kernel_kfold(segmentations, iohandler, output, next(kf), 0)
    else:
        joblib.Parallel(n_jobs=kf.ngpus, verbose=(1 if segmentations.verbose else 0))(
            joblib.delayed(compute_entropy_kernel_kfold)(
                segmentations, iohandler, output, chunk, gpu
            )
            for gpu, chunk in enumerate(kf)
        )


def run_entropy(
    iohandler: IOHandler,
    regexp: str,
    output: str,
    ncpus: int,
    ngpus: int,
    dtype,
    kfold,
    verbose,
):
    segmentations = Segmentations(iohandler, regexp, dtype, ncpus, verbose)
    kf = KFoldEntropy(segmentations, ngpus) if kfold else None
    compute_entropy(segmentations, kf, iohandler, output)


def load_command(command):
    with open(command, "r") as f:
        return json.load(f)


def parse_args():
    parser = argparse.ArgumentParser("entropy")
    parser.add_argument("--regexp", help="Regular expression for segmentations")
    parser.add_argument("--output", help="Output path for entropy image")
    parser.add_argument("--command", help="JSON command to run")
    parser.add_argument(
        "--ncpus", type=int, default=os.cpu_count(), help="Number of CPUs to use"
    )
    parser.add_argument("--ngpus", type=int, default=1, help="Number of GPUs to use")
    parser.add_argument("--dtype", default="uint16", help="Data type for segmentations")
    parser.add_argument("--verbose", action="store_true", help="Print debug info")
    parser.add_argument(
        "--kfold", action="store_true", help="Run kfold cross validation"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    if not args.debug:
        global ic
        ic = lambda *args, **kwargs: None

    if args.command:
        commands = load_command(args.command)
    else:
        commands = [{"regexp": args.regexp, "output": args.output}]

    iohandler = IOHandlerNibabel()
    dtype = np.dtype(args.dtype)

    for command in commands:
        regexp = command["regexp"]
        output = command["output"]
        if not os.path.exists(command["output"]) or args.force:
            if os.path.dirname(output) != "":
                os.makedirs(os.path.dirname(output), exist_ok=True)
            run_entropy(
                iohandler,
                regexp,
                output,
                args.ncpus,
                args.ngpus,
                dtype,
                args.kfold,
                args.verbose,
            )


if "__main__" == __name__:
    main()
