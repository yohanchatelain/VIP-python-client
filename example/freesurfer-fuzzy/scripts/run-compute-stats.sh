#!/bin/bash

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

SCRIPT=${ROOT}/compute_stats.py
DIRECTORY=${ROOT}/stats
FSGD=${ROOT}/scripts/fsgd_cort_group_HC_PDnonMCI_baseline.fsgd
JSON=${ROOT}/scripts/json_data.json

# Compute mean
STAT=mean
DIR=${DIRECTORY}/aparc
for measure in area thickness volume; do
    echo $DIR $STAT $measure
    python3 ${SCRIPT} --directory ${DIRECTORY}/aparc --measure ${measure} \
        --level-analysis subject --hemi --fp-type float64 \
        --output="subject-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
    python3 ${SCRIPT} --directory ${DIRECTORY}/aparc --measure ${measure} \
        --level-analysis group --fsgd ${FSGD} --hemi --fp-type float64 \
        --output="group-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
done

DIR=${DIRECTORY}/aseg
measure=volume
echo $DIR $STAT $measure
python3 ${SCRIPT} --directory ${DIR} --measure ${measure} \
    --level-analysis subject --fp-type float64 \
    --output="subject-subcortical-${measure}-${STAT}.csv" --json-data=${JSON} --stats-type=$STAT
python3 ${SCRIPT} --directory ${DIR} --measure ${measure} \
    --level-analysis group --fsgd ${FSGD} --fp-type float64 \
    --output="group-subcortical-${measure}-${STAT}.csv" --json-data=${JSON} --stats-type=$STAT

# Compute standard deviation
STAT=std
DIR=${DIRECTORY}/aparc
for measure in area thickness volume; do
    echo $DIR $STAT $measure
    python3 ${SCRIPT} --directory ${DIRECTORY}/aparc --measure ${measure} \
        --level-analysis subject --hemi --fp-type float64 \
        --output="subject-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
    python3 ${SCRIPT} --directory ${DIRECTORY}/aparc --measure ${measure} \
        --level-analysis group --fsgd ${FSGD} --hemi --fp-type float64 \
        --output="group-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
done

DIR=${DIRECTORY}/aseg
measure=volume
echo $DIR $STAT $measure
python3 ${SCRIPT} --directory ${DIR} --measure ${measure} \
    --level-analysis subject --fp-type float64 \
    --output="subject-subcortical-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
python3 ${SCRIPT} --directory ${DIR} --measure ${measure} \
    --level-analysis group --fsgd ${FSGD} --fp-type float64 \
    --output="group-subcortical-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}

# Compute significant digits
STAT=sig
DIR=${DIRECTORY}/aparc
for measure in area thickness volume; do
    echo $DIR $STAT $measure
    python3 ${SCRIPT} --directory ${DIR} --measure ${measure} \
        --level-analysis subject --hemi --fp-type float16 \
        --output="subject-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
    python3 ${SCRIPT} --directory ${DIR} --measure ${measure} \
        --level-analysis group --fsgd ${FSGD} --hemi --fp-type float16 \
        --output="group-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
done

DIR=${DIRECTORY}/aseg
measure=volume
echo $DIR $STAT $measure
python3 ${SCRIPT} --directory ${DIR} --measure ${measure} \
    --level-analysis subject --fp-type float16 \
    --output="subject-subcortical-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
python3 ${SCRIPT} --directory ${DIR} --measure ${measure} \
    --level-analysis group --fsgd ${FSGD} --fp-type float16 \
    --output="group-subcortical-${measure}-${STAT}.csv" --stats-type=$STAT --json-data=${JSON}
