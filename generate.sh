#!/bin/bash

INFILE=$1
baseame="${INFILE%.*}"
dirname=$(dirname $INFILE)
./generate_diagram.py ${INFILE} -o ${baseame}.tex 

# Exit if diagram generation failed
if [ $? -ne 0 ]; then
    exit 1
fi

latex -interaction=batchmode -output-format=pdf -output-directory=${dirname} ${baseame}.tex 
