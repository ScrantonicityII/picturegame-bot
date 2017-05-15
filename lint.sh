#!/bin/bash
pylint3 src/**/*.py -d broad-except -d global-statement > pylint.txt
