#!/bin/bash
whichVBS="sswwAnalysis"

if [[ "$whichVBS" == "wzAnalysis" ]]; then
  BASE_DIRECTORY="/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerratewz"
else
  BASE_DIRECTORY="/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/50GeV"
fi

for dir in 1000; do
  for cutoff in 0000; do
  for file in ${BASE_DIRECTORY}/${dir}/${cutoff}/merge1/fillhisto_${whichVBS}_202*.root; do
    newfile=$(echo "$file" | sed "s/${whichVBS}_/${whichVBS}${dir}_/")
    mv "$file" "$newfile"
  done
  done
done
