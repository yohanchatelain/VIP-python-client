#!/bin/bash

#SBATCH --job-name=parallel-extract
#SBATCH --array=1-13
#SBATCH --output=parallel_extract_%A_%a.out
#SBATCH --error=parallel_extract_%A_%a.err
#SBATCH --time=05:00:00
#SBATCH --ntasks=128
#SBATCH --threads-per-core=1
#SBATCH --mem-per-cpu=500MB

# Change to the directory where the script is being executed
SLURM_SUBMIT_DIR=rep${SLURM_ARRAY_TASK_ID}

cd $SLURM_SUBMIT_DIR

# Define the source directory
SRC_DIR="./.archive"

# Find all .tgz files in the source directory
FILES=($SRC_DIR/*.tgz)

parallel --max-procs=128 'tar xf' ::: ${FILES[@]}
