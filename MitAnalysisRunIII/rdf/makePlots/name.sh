#!/bin/bash

for file in /mnt/home/mghimiray/VBSStudies/Outputs_EFT/OriginalTT/merge2/fillhisto_sswwAnalysis_202*.root; do 
  newfile=$(echo "$file" | sed 's/sswwAnalysis_/sswwAnalysis1001_/') 
  mv "$file" "$newfile" 
done 
