#!/bin/bash

# Run from rep<n> directory

FIRST_VISIT=$1
SECOND_VISIT=$2
BASE=$3

mkdir -p base_template
export SUBJECTS_DIR=$(pwd) FS_LICENSE=$(realpath ../../../../license.txt)

# Step 1 - base template
# Data from json_data_base.json
# Freesurfer Zenodo 7916240
# Create an unbiased template from all time points for each subject and process it with recon-all
singularity exec -B $(realpath ../../../..):$(realpath ../../../..) $(realpath ~/lustre/freesurfer.sif) recon-all -base base_template/${BASE} -tp ${FIRST_VISIT} -tp ${SECOND_VISIT} -all
