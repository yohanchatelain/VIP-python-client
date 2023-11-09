# Run from rep<n> directory

SUBJECT=$1

mkdir -p base_template
export SUBJECTS_DIR=$(pwd) FS_LICENSE=$(realpath ../../../../license.txt)

# Step 1 - base template
# Data from json_data_base.json
# Freesurfer Zenodo 7916240
# Create an unbiased template from all time points for each subject and process it with recon-all
FIRST_VISIT=${SUBJECT}_ses-BL
SECOND_VISIT=${SUBJECT}_ses-V04
BASE=${SUBJECT}
singularity exec -B $(realpath ../../../..):$(realpath ../../../..) $(realpath ~/lustre/freesurfer.sif) recon-all -base base_template/${BASE} -tp ${FIRST_VISIT} -tp ${SECOND_VISIT} -all

# Step 2 - longitudinally processed timepoints
# Data from json_data_long.json
# Freesurfer Zenodo 7920788
# "-long" longitudinally process all timepoints (recon-all -long)
VISIT=${SUBJECT}_ses-BL
BASE=${SUBJECT}
singularity exec -B $(realpath ../../../..):$(realpath ../../../..) $(realpath ~/lustre/freesurfer.sif) recon-all -long -tp ${VISIT} base_template/${BASE} -all

# Step 3 - Qcache
# Data from json_data_long.json
# Freesurfer Zenodo 7920876
# save proprocessing script to submit jobs to the server later
VISIT=${SUBJECT}_ses-BL
BASE=${SUBJECT}
singularity exec -B $(realpath ../../../..):$(realpath ../../../..) $(realpath ~/lustre/freesurfer.sif) recon-all -long -tp ${VISIT} base_template/${BASE} -qcache
