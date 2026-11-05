#!/bin/sh

#root -l -b -q 'makeAllPlots.C("ssww", false, 2027,1014,"1500")'  
theAna="fillhisto_"
source /mnt/home/mghimiray/VBSStudies/cmsstyle/cmsstyle/scripts/setup_cmstyle
dirs=(
    1000
#    1000
#    1013
#    1014
#    1016
#    1022
#    1023
)

cutoffs=(
    0000
#    1000
#    1200
#    1500
#    2000
#    3000
)

years=(
    2027
#     2022
    # 2023
    # 2024
    # 2025
)

base="/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/50GeV"


# ============================================================
# Main merging loop
# ============================================================

for dir in "${dirs[@]}"
do
    # Automatically becomes:
    # 1010 -> sswwAnalysis1010
    # 1016 -> sswwAnalysis1016
    theCondor="sswwAnalysis${dir}"

    for cutoff in "${cutoffs[@]}"
    do
        indir="${base}/${dir}/${cutoff}/merge1"
        outdir="${base}/${dir}/${cutoff}/merge2"

        if [[ ! -d "${indir}" ]]; then
            echo "Input directory not found: ${indir}"
            continue
        fi

        mkdir -p "${outdir}"

        for theYear in "${years[@]}"
        do
            echo
            echo "=================================================="
            echo "Analysis : ${theCondor}"
            echo "Directory: ${dir}"
            echo "Cutoff   : ${cutoff}"
            echo "Year     : ${theYear}"
            echo "=================================================="

            if [[ "${theYear}" == "2027" ]]; then

                for i in $(seq 0 600)
                do
                    # ----------------------------------------
                    # Normal 1D files
                    # ----------------------------------------

                    if [[ -f "${indir}/${theAna}${theCondor}_20220_${i}.root" ]]; then

                        echo "Merging variable ${i}"

                        hadd -f \
                            "${outdir}/${theAna}${theCondor}_${theYear}_${i}.root" \
                            ${indir}/${theAna}${theCondor}_2022?_${i}.root \
                            ${indir}/${theAna}${theCondor}_2023?_${i}.root \
                            ${indir}/${theAna}${theCondor}_2024?_${i}.root \
                            ${indir}/${theAna}${theCondor}_2025?_${i}.root
                    fi

                    # ----------------------------------------
                    # 2D files
                    # ----------------------------------------

                    if [[ -f "${indir}/${theAna}${theCondor}_20220_${i}_2d.root" ]]; then

                        echo "Merging 2D variable ${i}"

                        hadd -f \
                            "${outdir}/${theAna}${theCondor}_${theYear}_${i}_2d.root" \
                            ${indir}/${theAna}${theCondor}_2022?_${i}_2d.root \
                            ${indir}/${theAna}${theCondor}_2023?_${i}_2d.root \
                            ${indir}/${theAna}${theCondor}_2024?_${i}_2d.root \
                            ${indir}/${theAna}${theCondor}_2025?_${i}_2d.root
                    fi
                done

            else

                for i in $(seq 0 600)
                do
                    # ----------------------------------------
                    # Normal 1D files
                    # ----------------------------------------

                    if [[ -f "${indir}/${theAna}${theCondor}_${theYear}0_${i}.root" ]]; then

                        echo "Merging variable ${i}"

                        hadd -f \
                            "${outdir}/${theAna}${theCondor}_${theYear}_${i}.root" \
                            ${indir}/${theAna}${theCondor}_${theYear}?_${i}.root
                    fi

                    # ----------------------------------------
                    # 2D files
                    # ----------------------------------------

                    if [[ -f "${indir}/${theAna}${theCondor}_${theYear}0_${i}_2d.root" ]]; then

                        echo "Merging 2D variable ${i}"

                        hadd -f \
                            "${outdir}/${theAna}${theCondor}_${theYear}_${i}_2d.root" \
                            ${indir}/${theAna}${theCondor}_${theYear}?_${i}_2d.root
                    fi
                done

            fi
        done
    done
done

echo
echo "DONE"
