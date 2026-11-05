#!/usr/bin/env bash

# Usage examples:
#   ./submit_cis.sh 2022
#   ./submit_cis.sh 2022 1000 1002
#   ./submit_cis.sh 2022 1000 1003
#
# Current convention kept from your script:
#   $1 = year
#   $3 = sample
#


whichyear=$1
sample=$2
which_job=(0 1 2 3 4 5)

declare -A year_process_map
year_keys=()


if [[ "$sample" = "1002" ]]; then

    case "$whichyear" in
        2022)
            year_keys=("20220" "20221")
            year_process_map["20220"]="110"
            year_process_map["20221"]="210"
            ;;
        2023)
            year_keys=("20230" "20231")
            year_process_map["20230"]="310"
            year_process_map["20231"]="410"
            ;;
        2024)
            year_keys=("20240")
            year_process_map["20240"]="510"
            ;;
        2025)
            year_keys=("20250")
            year_process_map["20250"]="510"
            ;;
        *)
            echo "Invalid year: $whichyear"
            echo "Usage: ./submit_cis.sh [2022|2023|2024|2025] [unused] [sample]"
            exit 1
            ;;
    esac

elif [[ "$sample" = "1003" ]]; then

    case "$whichyear" in
        2022)
            year_keys=("20220" "20221")
            year_process_map["20220"]="136"
            year_process_map["20221"]="236"
            ;;
        2023)
            year_keys=("20230" "20231")
            year_process_map["20230"]="336"
            year_process_map["20231"]="436"
            ;;
        2024)
            year_keys=("20240")
            year_process_map["20240"]="536"
            ;;
        2025)
            year_keys=("20250")
            year_process_map["20250"]="536"
            ;;
        *)
            echo "Invalid year: $whichyear"
            echo "Usage: ./submit_cis.sh [2022|2023|2024|2025] [unused] [sample]"
            exit 1
            ;;
    esac

else

    case "$whichyear" in
        2022)
            year_keys=("20220" "20221")
            year_process_map["20220"]="100 101 108 109 111 112 113 1011 1012 1031 1032 1033 1042 1043"
            year_process_map["20221"]="200 201 208 209 211 212 213 1034 1035 1036 1044 1045 1046"
            ;;
        2023)
            year_keys=("20230" "20231")
            year_process_map["20230"]="300 301 308 309 311 312 313 1032 1042"
            year_process_map["20231"]="400 401 408 409 411 412 413 1033 1043"
            ;;
        2024)
            year_keys=("20240")
            year_process_map["20240"]="500 501 508 509 511 512 513 525 526 527 528 542 543 1032 1033 1034 1035 1036 1037 1038 1042 1043 1044 1045 1046 1047 1048"
            ;;
        2025)
            year_keys=("20250")
            year_process_map["20250"]="500 501 508 509 511 512 513 525 526 527 528 542 543 1031 1032 1033 1034 1035 1036 1041 1042 1043 1044 1045 1046"
            ;;
        *)
            echo "Invalid year: $whichyear"
            echo "Usage: ./submit_cis.sh [2022|2023|2024|2025] [unused] [sample]"
            exit 1
            ;;
    esac

fi

for year in "${year_keys[@]}"; do
    echo "Year: $year"

    processes="${year_process_map[$year]}"

    for process in $processes; do
        for job in "${which_job[@]}"; do
            echo "Submitting: Year=$year, Process=$process, Job=$job, Sample=$sample"
            sbatch -p INTEL_PHI \
                   --time=70:00:00 \
                   --cpus-per-task=1 \
                   --nodes=1 \
                   --job-name="vbsmatrixmethod_${year}_${process}_${job}" \
                   --output="log/vbs__${year}_${process}_${job}.out" \
                   --error="log/vbs__${year}_${process}_${job}.err" \
                   submit_cis_fake.sh "$year" "$process" "$job" "$sample"
        done
    done
done