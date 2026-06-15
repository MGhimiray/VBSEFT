#!/bin/bash

for dir in 1012; do
  for file in /mnt/home/mghimiray/VBSStudies/Outputs_EFT/OriginalTT/${dir}/1000/merge1/fillhisto_sswwAnalysis_202*.root; do
    newfile=$(echo "$file" | sed "s/sswwAnalysis_/sswwAnalysis${dir}_/")
    mv "$file" "$newfile"
  done
done
