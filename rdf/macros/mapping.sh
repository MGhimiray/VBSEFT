#!/bin/bash

whichVBS="sswwAnalysis"

for dir in 1000; do

  for cutoff in 0000; do

    for samples in 1020 1021 1022 1023 1030 1031 1032 1033 1034 1040 1041 1042 1043; do

      newsamples=$((samples + 1000))

      for jobs in {0..14}; do


        if [[ "$whichVBS" == "wzAnalysis" ]]; then


          mv \
          /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/50GeV/${dir}/${cutoff}/histo/fillhisto_wzAnalysis/fillhisto_wzAnalysis${dir}_sample${samples}_year20260_job${jobs}.root \
          /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/50GeV/${dir}/${cutoff}/histo/fillhisto_wzAnalysis/fillhisto_wzAnalysis${dir}_sample${newsamples}_year20250_job${jobs}.root


        elif [[ "$whichVBS" == "sswwAnalysis" ]]; then


          mv \
          /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/50GeV/${dir}/${cutoff}/histo/fillhisto_sswwAnalysis/fillhisto_sswwAnalysis${dir}_sample${samples}_year20260_job${jobs}.root \
          /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/50GeV/${dir}/${cutoff}/histo/fillhisto_sswwAnalysis/fillhisto_sswwAnalysis${dir}_sample${newsamples}_year20250_job${jobs}.root


        else

          echo "Unknown analysis: $whichVBS"
          exit 1

        fi


      done

    done

  done

done