#!/bin/bash
shopt -s nullglob

for file in /mnt/home/mghimiray/VBSStudies/Outputs_EFT/Fakerate/output/fillhisto_fakeAnalysis1001_sample536_year20240_job*.root*; do
  newfile="${file/fakeAnalysis1001/fakeAnalysis1003}"
  mv -- "$file" "$newfile"
done
