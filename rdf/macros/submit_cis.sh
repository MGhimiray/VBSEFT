#!/bin/bash

# Usage:
# ./submit_cis.sh year variable
# year = 2022, 2023, 2024, 2025, or 2027
# 2027 means process all years

whichyear=$1
variable=$2
makedataCards=$((variable - 1000))

declare -A year_process_map

which_job="0 1 2 3"

if [ "$whichyear" = "2027" ]; then

    # Process all years
    year_process_map["20220"]="1001 1002 1011 1012 1021 1022 1023 1031 1032 1033 1042 1043"
    year_process_map["20221"]="1024 1025 1026 1034 1035 1036 1044 1045 1046"

    year_process_map["20230"]="1022 1032 1042"
    year_process_map["20231"]="1023 1033 1043"

    year_process_map["20240"]="1022 1023 1024 1025 1026 1027 1028 1032 1033 1034 1035 1036 1037 1038 1042 1043 1044 1045 1046 1047 1048"
    year_process_map["20250"]="1021 1022 1023 1024 1025 1026 1031 1032 1033 1034 1035 1036 1041 1042 1043 1044 1045 1046"
    year_process_map["20260"]="1020 1021 1023 1030 1031 1033 1034 1040 1041 1043"

elif [ "$whichyear" = "2023" ]; then

    year_process_map["20230"]="1022 1032 1042"
    year_process_map["20231"]="1023 1033 1043"

elif [ "$whichyear" = "2024" ]; then

    year_process_map["20240"]="1022 1023 1024 1025 1026 1027 1028 1032 1033 1034 1035 1036 1037 1038 1042 1043 1044 1045 1046 1047 1048"

elif [ "$whichyear" = "2022" ]; then

    year_process_map["20220"]="1001 1002 1011 1012 1021 1022 1023 1031 1032 1033 1042 1043"
    year_process_map["20221"]="1024 1025 1026 1034 1035 1036 1044 1045 1046"

elif [ "$whichyear" = "2025" ]; then

    year_process_map["20250"]="1021 1022 1023 1024 1025 1026 1031 1032 1033 1034 1035 1036 1041 1042 1043 1044 1045 1046"

elif [ "$whichyear" = "2026" ]; then

    year_process_map["20260"]="1020 1021 1022 1023 1030 1031 1032 1033 1034 1040 1041 1042 1043"
else
    echo "Invalid year: $whichyear"
    echo "Allowed values: 2022, 2023, 2024, 2025, 2027"
    exit 1
fi

cutoff="0000"

mkdir -p log

for year in "${!year_process_map[@]}"; do
    echo "Year: $year"

    processes="${year_process_map[$year]}"

    for process in $processes; do
        for jobs in $which_job; do


            echo "Submitting: Year=$year, Process=$process, Job=$jobs, Cutoff=$cutoff, MakeDataCards=$makedataCards"

            sbatch -p INTEL_HASWELL \
                --time=70:00:00 \
                --cpus-per-task=1 \
                --nodes=1 \
                --job-name="${makedataCards}_fakerrate_${year}_${process}_${jobs}" \
                --output="log/vbs__${year}_${process}_${jobs}.out" \
                --error="log/vbs__${year}_${process}_${jobs}.err" \
                submit_cis_analysis.sh \
                "$year" \
                "$process" \
                "$jobs" \
                "$cutoff" \
                "$makedataCards"
        done
    done
done


