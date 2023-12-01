#!/bin/bas

# Check repetitions number for each subject

PROJECT_ROOT=$HOME/projects/rrg-glatard/ychatel/living-park/VIP-python-client/
INPUT_JSON=$PROJECT_ROOT/example/freesurfer-fuzzy/scripts/json_data.json

if [[ ! -f $INPUT_JSON ]]; then
    echo "json file not found: ${INPUT_JSON}"
    exit 1
fi


PATNO=$(jq -r '(.PATNO_id | keys[])' "$INPUT_JSON")
for i in `seq 1 13`; do
    COUNTER=1
    MISSING_ARCHIVE=0
    MISSING_SUBJECTS=0

    for patno in $PATNO; do
        echo -ne "\r${COUNTER}/${#PATNO[@]}"
        ((COUNTER++))
        subject=$(jq -r ".PATNO_id[\"$patno\"]" "$INPUT_JSON")

        if [[ ! -f "rep${i}/.archive/${subject}.tgz" ]]; then
            ((MISSING_ARCHIVE++))
        fi 
        
        if [[ ! -d "rep${i}/${subject}" ]]; then
            ((MISSING_SUBJECTS++))
        fi 
        
    done

    echo -e "\nRepetititon $i: missing ${MISSING_ARCHIVE} archives"
    echo -e "Repetititon $i: missing ${MISSING_SUBJECTS} subjects\n"
    
done 

# Check repetitions for which recon-all has failed

# Check repetitions for which base-template has failed

# Check repetitions for which longitudinal has failed