#!/bin/bash

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

SCRIPT=${ROOT}/compute_stats.py
DIRECTORY=${ROOT}/stats
FSGD=${ROOT}/scripts/fsgd_cort_group_HC_PDnonMCI_baseline.fsgd

# plot cortical thickness std
python3 ${SCRIPT} --directory ${DIRECTORY} --measure thickness --fsgd ${FSGD} --fp-type float64 --xaxis='Cortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Cortical thickness' --output='cortical-thickness-std' --stats-type='std'

# plot cortical volume std
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float64 --xaxis='Cortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Cortical volume' --output='cortical-volume-std' --stats-type='std'

# plot subcortical volume std
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float64 --xaxis='Subcortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Subcortical volume' --output='subcortical-volume-std' --stats-type='std'

# plot cortical thickness sig
python3 ${SCRIPT} --directory ${DIRECTORY} --measure thickness --fsgd ${FSGD} --fp-type float16 --xaxis='Cortical parcellation' --yaxis='Significant digits' --title='Cortical thickness' --output='cortical-thickness-sig'

# plot cortical volume sig
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float16 --xaxis='Cortical parcellation' --yaxis='Significant digits' --title='Cortical volume' --output='cortical-volume-sig'

# plot subcortical volume sig
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float16 --xaxis='Subcortical parcellation' --yaxis='Significant digits' --title='Subcortical volume' --output='subcortical-volume-sig'
