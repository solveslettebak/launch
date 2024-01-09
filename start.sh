#!/usr/bin/bash -l
cd /nfs/Linacshare_controlroom/MCR/launcher

cd modules

output=$(python prelauncher.py)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    conda activate $output
else
    echo "No venv setting found"
fi

cd ..

python launcher.py
