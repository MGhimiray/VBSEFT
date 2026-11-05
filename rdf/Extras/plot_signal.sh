#!/usr/bin/env bash

luminosity=280.0
drawRatio=false
logY=false
rebin=1

years=(
    20220
    20221
    20230
    20231
    20240
    20250
)

for cutoff in 0000 1000 1200 1500 2000 3000; do
    for variable in 1022 ; do
        for operator in T0 T1 T2 S0 M0 M1 M7; do

            base="/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/${variable}/${cutoff}/datacards"

            merged_dir="${base}/merged"
            mkdir -p "${merged_dir}"

            merged_input="${merged_dir}/output_sswwAnalysis${variable}_${operator}_allYears_bin0.root"

            input_files=()

            echo
            echo "=================================================="
            echo "Variable: ${variable}"
            echo "Operator: ${operator}"
            echo "Cutoff  : ${cutoff}"
            echo "=================================================="

            for year in "${years[@]}"; do

                year_input="${base}/output_sswwAnalysis${variable}_${operator}_${year}_bin0.root"

                if [[ -f "${year_input}" ]]; then
                    echo "Adding year ${year}: ${year_input}"
                    input_files+=("${year_input}")
                else
                    echo "WARNING: Missing year ${year}:"
                    echo "  ${year_input}"
                fi

            done

            if [[ ${#input_files[@]} -eq 0 ]]; then
                echo "ERROR: No input files found for ${variable} ${operator}"
                continue
            fi

            echo "Merging ${#input_files[@]} files into:"
            echo "  ${merged_input}"

            hadd -f "${merged_input}" "${input_files[@]}"

            if [[ $? -ne 0 || ! -f "${merged_input}" ]]; then
                echo "ERROR: hadd failed for ${variable} ${operator}"
                continue
            fi

            output="${variable}_${operator}_${cutoff}.png"

            echo "Creating plot:"
            echo "  plots/${output}"

            root -l -b -q \
                "plot_signal.C(\"${merged_input}\",\"${output}\",\"${operator}\",${variable},${luminosity},${drawRatio},${logY},${rebin})"

        done
    done
done
