FS_DOCKER=freesurfer/freesurfer:7.3.1
OUTPUT_DIR=outputs
REPETITIONS=$(find ${OUTPUT_DIR} -type d -name "rep*")
STATS_DIR=$PWD/stats

mkdir -p ${STATS_DIR}

# aseg:
# Automatic subcortical segmentation of a brain volume is based upon the existence of an atlas containing probablistic information on the location of structures. This is decribed here:
# Whole Brain Segmentation: Automated Labeling of Neuroanatomical Structures in the Human Brain, Fischl et al., (2002). Neuron, 33:341-355.
for rep in $REPETITIONS; do
    SUBJECTS=$(find ${rep} -type d -name "sub-*" -printf "%f ")
    docker run -v $PWD:$PWD -e SUBJECTS_DIR=$PWD/${rep} ${FS_DOCKER} asegstats2table --all-segs --subjects ${SUBJECTS} --tablefile ${STATS_DIR}/$(basename ${rep})-cortical-volume.tsv
done

# aparc
# technique for automatically assigning a neuroanatomical label to each location on a cortical surface model based on probabilistic information
# Destrieux C, Fischl B, Dale A, Halgren E. Automatic parcellation of human cortical gyri and sulci using standard anatomical nomenclature.
# Neuroimage. 2010 Oct 15;53(1):1-15. doi: 10.1016/j.neuroimage.2010.06.010. Epub 2010 Jun 12. PMID: 20547229; PMCID: PMC2937159.
for rep in $REPETITIONS; do
    SUBJECTS=$(find ${rep} -type d -name "sub-*" -printf "%f ")
    for hemi in lh rh; do
        for measure in thickness volume thickness thicknessstd meancurv gauscurv foldind curvind; do
            docker run -v $PWD:$PWD -e SUBJECTS_DIR=$PWD/${rep} ${FS_DOCKER} aparcstats2table --subjects ${SUBJECTS} --tablefile ${STATS_DIR}/$(basename ${rep})-${hemi}-${measure}.tsv \
                --hemi ${hemi} -m ${measure} -p aparc.a2009s
        done
    done
done
