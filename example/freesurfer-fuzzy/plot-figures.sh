#!/bin/bash

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

SCRIPT=${ROOT}/compute_stats.py
DIRECTORY=${ROOT}/stats
FSGD=${ROOT}/scripts/fsgd_cort_group_HC_PDnonMCI_baseline.fsgd

# Surface area
# plot surface area mean
python3 ${SCRIPT} --directory ${DIRECTORY} --measure area --fsgd ${FSGD} --fp-type float64 --xaxis='Region' --yaxis='Standard deviation (log)' --log-yaxis --title='Surface area' --output='surface-area-mean' --stats-type='mean'

# plot surface area std
python3 ${SCRIPT} --directory ${DIRECTORY} --measure area --fsgd ${FSGD} --fp-type float64 --xaxis='Region' --yaxis='Standard deviation (log)' --log-yaxis --title='Surface area' --output='surface-area-std' --stats-type='std'

# plot surface area sig
python3 ${SCRIPT} --directory ${DIRECTORY} --measure area --fsgd ${FSGD} --fp-type float16 --xaxis='Region' --yaxis='Significant digits' --title='Surface area' --output='surface-area-sig' --stats-type='sig'

# Cortical thickness
# plot cortical thickness mean
python3 ${SCRIPT} --directory ${DIRECTORY} --measure thickness --fsgd ${FSGD} --fp-type float64 --xaxis='Cortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Cortical thickness' --output='cortical-thickness-mean' --stats-type='mean'

# plot cortical thickness std
python3 ${SCRIPT} --directory ${DIRECTORY} --measure thickness --fsgd ${FSGD} --fp-type float64 --xaxis='Cortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Cortical thickness' --output='cortical-thickness-std' --stats-type='std'

# plot cortical thickness sig
python3 ${SCRIPT} --directory ${DIRECTORY} --measure thickness --fsgd ${FSGD} --fp-type float16 --xaxis='Cortical parcellation' --yaxis='Significant digits' --title='Cortical thickness' --output='cortical-thickness-sig'

# Cortical volume
# plot cortical volume mean
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float64 --xaxis='Cortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Cortical volume' --output='cortical-volume-mean' --stats-type='mean'

# plot cortical volume std
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float64 --xaxis='Cortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Cortical volume' --output='cortical-volume-std' --stats-type='std'

# plot cortical volume sig
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float16 --xaxis='Cortical parcellation' --yaxis='Significant digits' --title='Cortical volume' --output='cortical-volume-sig'

# Subcortical volume
# plot subcortical volume mean
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float64 --xaxis='Subcortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Subcortical volume' --output='subcortical-volume-mean' --stats-type='mean'

# plot subcortical volume std
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float64 --xaxis='Subcortical parcellation' --yaxis='Standard deviation (log)' --log-yaxis --title='Subcortical volume' --output='subcortical-volume-std' --stats-type='std'

# plot subcortical volume sig
python3 ${SCRIPT} --directory ${DIRECTORY} --measure volume --fsgd ${FSGD} --fp-type float16 --xaxis='Subcortical parcellation' --yaxis='Significant digits' --title='Subcortical volume' --output='subcortical-volume-sig'
