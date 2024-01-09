#!/usr/bin/bash -l

# This should preferably just be in start.sh, but all MCR desktops are set up to start this file currently.. 

cd /nfs/Linacshare_controlroom/MCR/launcher

cd modules

output=$(python prelauncher.py)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    conda activate $output
else
    echo "No venv setting found. Trying pytools"
    conda activate pytools
fi

cd ..

python launcher.py
