#!/bin/bash

INFILE=$1
baseame="${INFILE%.*}"
dirname=$(dirname $INFILE)
./diagram_generator.py ${INFILE} -o ${baseame}.tex 
latex -interaction=batchmode -output-format=pdf -output-directory=${dirname} ${baseame}.tex 
