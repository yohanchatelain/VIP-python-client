#!/bin/bash

PROJECT_ROOT=$HOME/projects/rrg-glatard/ychatel/living-park/VIP-python-client/
FS_SIF=$PROJECT_ROOT/freesurfer-7.3.1.sif

export FS_LICENSE=$PROJECT_ROOT/freesurfer-fuzzy/license.txt

# Run from rep<n> directory
REPETITION=$1
FIRST_VISIT=$2
SECOND_VISIT=$3
BASE=$4

cd /scratch/ychatel/living-park/VIP-python-client/example/freesurfer-fuzzy/${REPETITION}

mkdir -p base_template
export SUBJECTS_DIR=$(pwd)


# Step 1 - base template
# Data from json_data_base.json
# Freesurfer Zenodo 7916240
# Create an unbiased template from all time points for each subject and process it with recon-all
apptainer exec -B $(realpath ../../../..):$(realpath ../../../..) ${FS_SIF} recon-all -base base_template/${BASE} -tp ${FIRST_VISIT} -tp ${SECOND_VISIT} -all
