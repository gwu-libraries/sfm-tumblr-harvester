#!/usr/bin/env bash

if [ $SFM_REQS != "requirements" ]; then
    echo "Uninstalling requirements.txt."
    pip uninstall -r requirements/release.txt -y
    echo "Upgrading common.txt"
    pip install -r requirements/common.txt --upgrade
    echo "Installing $SFM_REQS.txt"
    pip install -r requirements/$SFM_REQS.txt
fi
