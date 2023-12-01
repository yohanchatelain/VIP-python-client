#!/bin/bash


function difference() {
    python3 -c """
from os.path import basename as bs;
tar = set(bs(ar).split('.')[0].strip() for ar in open('tar.txt','r').readlines());
sub = set(bs(sub).strip() for sub in open('sub.txt','r').readlines());
diff = set.symmetric_difference(tar,sub);
print(' '.join(diff)) if diff else print('')
"""
}

for i in `seq 1 13`; do
    echo $i
    FILES=(rep${i}/.archive/*.tgz)
    SUBJECTS=(rep${i}/sub-*)
    echo ${FILES[@]} > tar.txt
    echo ${SUBJECTS[@]} > sub.txt
    for f in $(difference); do
        echo "Extract rep${i}/.archive/${f}.tgz to rep${i}/$f"
        tar xf rep${i}/.archive/${f}.tgz -C rep${i}/$f
    done
done
