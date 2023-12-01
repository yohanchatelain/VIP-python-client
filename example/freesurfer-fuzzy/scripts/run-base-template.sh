#!/bin/bash

#set -xe

#SBATCH --job-name=run-base-template
#SBATCH --array=1-13
#SBATCH --output=run-base-template_%A_%a.out
#SBATCH --error=run-base-template_%A_%a.err
#SBATCH --time=72:00:00
#SBATCH --ntasks=256
#SBATCH --threads-per-core=1
#SBATCH --mem-per-cpu=16GB

REPETITION=rep${SLURM_ARRAY_TASK_ID}

PROJECT_ROOT=$HOME/projects/rrg-glatard/ychatel/living-park/VIP-python-client/
SUBJECT_DIRS=$PROJECT_ROOT/example/freesurfer-fuzzy/vip_outputs/freesurfer-fuzzy/${REPETITION}
FS_SIF=$PROJECT_ROOT/freesurfer-7.3.1.sif
INPUT_JSON=$PROJECT_ROOT/example/freesurfer-fuzzy/scripts/json_data_base.json

cd $SUBJECT_DIRS

DST_LICENSE_DIR=/etc/license
DST_LICENSE_PATH=$DST_LICENSE_DIR/license.txt
DST_HOME_DIR=/home/
DST_SUBJECT_DIRS=$DST_HOME_DIR
SRC_HOME_DIR=$SUBJECT_DIRS
SRC_LICENSE_DIR=${PROJECT_ROOT}

# Read the keys (assuming all dictionaries have the same keys)
PATNO=$(jq -r '(.first_visit | keys[])' "$INPUT_JSON")

COUNTER=1

rm -f to_run

# Iterate over the keys
for patno in $PATNO; do
    echo -ne "\r${COUNTER}/${#PATNO[@]}"
    ((COUNTER++))
    # Extract corresponding values from each dictionary
    first_visit=$(jq -r ".first_visit[\"$patno\"]" "$INPUT_JSON")
    second_visit=$(jq -r ".second_visit[\"$patno\"]" "$INPUT_JSON")
    PATNO_base=$(jq -r ".PATNO_base[\"$patno\"]" "$INPUT_JSON")

        # Check if both files exist
    if [[ -d "$first_visit" && -d "$second_visit" ]]; then
        echo "apptainer -B ${SRC_LICENSE_DIR}:${DST_LICENSE_DIR} -B ${SRC_HOME_DIR}:${DST_HOME_DIR}  --env SUBJECT_DIRS=${DST_SUBJECT_DIRS} --env FS_LICENSE=${DST_LICENSE_PATH} ${FS_SIF} recon-all -all -base ${PATNO_base} -tp ${first_visit} -tp ${second_visit}" >> to_run
    else
        if [[ ! -d "$first_visit" ]]; then
            echo "Error: $PWD/$first_visit is missing"
        fi
        if [[ ! -d "$second_visit" ]]; then
            echo "Error: $PWD/$second_visit is missing"
        fi
    fi
done

cat to_run | parallel --max-procs=128 '{}'