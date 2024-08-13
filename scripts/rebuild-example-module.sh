#!/bin/bash

pushd lib/example-module
    if test -d _build; then
        rm -r _build
        rmdir _build
    fi
    mkdir _build && cd _build
    cmake .. -DCMLIB_DIR=https://github.com/cmakelib/cmakelib.git
    make
popd