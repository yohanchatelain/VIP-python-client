FS_DOCKER=freesurfer/freesurfer:7.3.1
REPETITIONS=$(find . -type d -name "rep*")

for rep in $REPETITIONS; do
    SUBJECTS=$(find ${rep} -type d -name "sub-*" -printf "%f ")
    docker run -v $PWD:$PWD -e SUBJECTS_DIR=$PWD/${rep} ${FS_DOCKER} asegstats2table --subjects ${SUBJECTS} --tablefile $PWD/${rep}.tsv
done
