#!/bin/bash

set -xe

# Job id of the current task
# SLURM_JOB_ID=36
# Job id corresponding to the first job of the array
# SLURM_ARRAY_JOB_ID=36 (37,38)
# Index of the current task
# SLURM_ARRAY_TASK_ID=1
# Number of tasks in the array
# SLURM_ARRAY_TASK_COUNT=3
# Highest index of the array
# SLURM_ARRAY_TASK_MAX=3
# Lowest index of the array
# SLURM_ARRAY_TASK_MIN=1

if [ -z "${SLURM_ARRAY_TASK_ID}" ]; then
    # Simulate a slurm job array with one task
    SLURM_ARRAY_TASK_COUNT=1
    SLURM_ARRAY_TASK_ID=1
fi
REPETITION=$SLURM_ARRAY_TASK_ID

# Initialize a variable to indicate whether --dry-run is set to false by default
dry_run=false

# Check if the --dry-run argument is passed
while [[ $# -gt 0 ]]; do
    case "$1" in
    --dry-run)
        dry_run=true
        shift # Remove the argument from the list of arguments
        ;;
    --input-json)
        INPUT_JSON="$2"
        shift # Remove the argument from the list of arguments
        shift # Remove the value from the list of arguments
        ;;
    *)
        # Handle other arguments here if needed
        shift # Remove the argument from the list of arguments
        ;;
    esac
done

# Check the value of dry_run
if [ "$dry_run" = true ]; then
    DRY_RUN="--dry-run"
else
    DRY_RUN=""
fi

PROJECT_ROOT=$HOME/projects/rrg-glatard/ychatel/living-park/VIP-python-client/
ARCHIVE_PATH=$PROJECT_ROOT/example/freesurfer-fuzzy/vip_outputs/freesurfer-fuzzy
PYTHON_SCRIPT=$PROJECT_ROOT/example/freesurfer-fuzzy/scripts/run-base-template.py
FS_SIF=$PROJECT_ROOT/freesurfer-7.3.1.sif

if [ -z "$INPUT_JSON" ]; then
    INPUT_JSON=$PROJECT_ROOT/example/freesurfer-fuzzy/scripts/json_data_base.json
fi

OUTPUT_DIR=/scratch/ychatel/VIP-python-client/example/freesurfer-fuzzy/vip_outputs/freesurfer-fuzzy/rep${REPETITION}

# Run from rep<n> directory
cd ${OUTPUT_DIR}

# Step 1 - base template
# Data from json_data_base.json
# Freesurfer Zenodo 7916240
# Create an unbiased template from all time points for each subject and process it with recon-all
python3 $PYTHON_SCRIPT --fs-image ${FS_SIF} --input ${INPUT_JSON} \
    --repetition ${REPETITION} --archive-dir ${ARCHIVE_PATH}/rep${REPETITION} \
    --output-dir ${OUTPUT_DIR} --src-license-dir ${PROJECT_ROOT} --src-home ${PWD} ${DRY_RUN}
