# Entropy QC analysis

## Structure of the directory

```bash
.
├── archive
├── entropy
├── entropy_compressed
├── entropy.json
├── gif
├── README.md
├── scripts
└── std_entropy.npz
```

- archive: Contains the tar files 
- entropy: Contains the global and leave-one-out (LOO) entropy computations.
Each entropy is saved as a Nifti file, postfixed with `_entropy`.
Global entropy are stored at the root the entropy/. LOO entropies are stored in 
directory with the subject+visit as name. 
- entropy_compressed: Contains the packed LOO entropies in one `npz` file.
- gif: Contains the GIF made from the `aseg.a2009s+aparc.mgz` segmentations files of MCA repetitions.
gif/png contains the frames for each GIF.
- scripts: Contains the scripts used to make the entropy and gif.
    * `generate_entropy_json.py`: Generates the `entropy.json` file used by `compute_entropy.py`.
    * `compute_entropy.py`: Generates the global and loo entropies
    * `make_compressed_entropy.py`: Generates the packed loo entropies
    * `compute_std_entropy.py`: Compute standard-deviation across loo entropies
    * `make_gif.py`: Generates GIF from `aseg.a2009s+aparc.mgz` segmentations files.
