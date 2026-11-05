#!/bin/bash

# Usage:
# ./submit_cisEFT.sh 2022 1001
# ./submit_cisEFT.sh 2027 1001   # run all years

whichyear=$1
variable=$2

makedataCards=$((variable - 1000))

declare -A year_process_map

which_job="0 1 2 3"

if [ "$whichyear" = "2027" ]; then

    # Run all available years
    year_process_map["20220"]="193 194 196 197 198 199 1990 1991 1992 1993 1994 1995 1996 1997"
    year_process_map["20221"]="293 294 296 297 298 299 2990 2991 2992 2993 2994 2995 2996 2997"

    year_process_map["20230"]="393 394 396 397 398 399 3990 3991 3992 3993 3994 3995 3996 3997"
    year_process_map["20231"]="493 494 496 497 498 499 4990 4991 4992 4993 4994 4995 4996 4997"

    year_process_map["20240"]="593 594 596 597 598 599 5990 5991 5992 5993 5994 5995 5996 5997"

    year_process_map["20250"]="693 694 696 697 698 699 6990 6991 6992 6993 6994 6995 6996 6997"

elif [ "$whichyear" = "2023" ]; then

    year_process_map["20230"]="393 394 396 397 398 399 3990 3991 3992 3993 3994 3995 3996 3997"
    year_process_map["20231"]="493 494 496 497 498 499 4990 4991 4992 4993 4994 4995 4996 4997"

elif [ "$whichyear" = "2024" ]; then

    year_process_map["20240"]="593 594 596 597 598 599 5990 5991 5992 5993 5994 5995 5996 5997"

elif [ "$whichyear" = "2022" ]; then

    year_process_map["20220"]="193 194 196 197 198 199 1990 1991 1992 1993 1994 1995 1996 1997"
    year_process_map["20221"]="293 294 296 297 298 299 2990 2991 2992 2993 2994 2995 2996 2997"

elif [ "$whichyear" = "2025" ]; then

    year_process_map["20250"]="693 694 696 697 698 699 6990 6991 6992 6993 6994 6995 6996 6997"

else
    echo "Invalid year: $whichyear"
    echo "Allowed values: 2022, 2023, 2024, 2025, 2027"
    exit 1
fi

#cutoff="0000 1000 1200 1500 2000 3000"

mkdir -p log

for cutoff in 0000; do
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
                --job-name="${makedataCards}_${cutoff}_vbsEFT_${year}_${process}_${jobs}" \
                --output="log/vbsEFT_${variable}_${year}_${process}_${jobs}.out" \
                --error="log/vbsEFT_${variable}_${year}_${process}_${jobs}.err" \
                submit_cis_analysis.sh \
                "$year" \
                "$process" \
                "$jobs" \
                "$cutoff" \
                "$makedataCards"
        done
    done
done
done



