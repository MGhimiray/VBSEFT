#!/bin/bash

for dir in 1013; do
  for cutoff in 0000 ; do
  for file in /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/${dir}/${cutoff}/merge1/fillhisto_sswwAnalysis_202*.root; do
    newfile=$(echo "$file" | sed "s/sswwAnalysis_/sswwAnalysis${dir}_/")
    mv "$file" "$newfile"
  done
  done
done
