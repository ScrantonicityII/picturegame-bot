#!/bin/bash
if [ ! -d data ]; then
    mkdir data
fi

./main.py "$@"
