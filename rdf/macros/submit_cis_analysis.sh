#!/bin/bash
#SBATCH --partition=INTEL_HASWELL
#SBATCH --time=70:00:00
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --job-name="vbstf"
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

source ~/.bashrc

conda activate myenv

years=$1
processes=$2
which_job=$3
cutoff=$4
makedatacards=$5
whichVBS=sswwAnalysis


if [[ "$whichVBS" == "wzAnalysis" ]]; then

    python3 wzAnalysis.py --year="$years" --process="$processes" --whichJob="$which_job" --cutOff="$cutoff" --makeDataCards="$makedatacards"

elif [[ "$whichVBS" == "sswwAnalysis" ]]; then

    python3 sswwAnalysis.py --year="$years" --process="$processes" --whichJob="$which_job" --cutOff="$cutoff" --makeDataCards="$makedatacards"

else

    echo "ERROR: Unknown analysis type: $whichVBS"
    exit 1

fi
