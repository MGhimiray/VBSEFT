#!/bin/bash

for dir in 1008 ; do
  for cutoff in 1000 1200 1500 2000 3000 ; do
  mkdir -p /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerratewz/${dir}/${cutoff}/histo/fillhisto_wzAnalysis/
  rm -f /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerratewz/${dir}/${cutoff}/histo/fillhisto_wzAnalysis/fillhisto_wzAnalysis*.root
  cp /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerratewz/${dir}/0000/histo/fillhisto_wzAnalysis/fillhisto_wzAnalysis*.root /mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerratewz/${dir}/${cutoff}/histo/fillhisto_wzAnalysis/
  done
done
