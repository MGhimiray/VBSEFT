#!/bin/sh
# to run: ./run_makeEFTDataCards.sh 1012 

export theOption=$2
#export theAna=sswwAnalysis$1
#export variable=$1

source /mnt/home/mghimiray/VBSStudies/cmsstyle/cmsstyle/scripts/setup_cmstyle
 
  for variable in 1008;do
  theAna=wzAnalysis$variable
  for cutoff in 0000 1000 1200 1500 2000 3000;
  do
  input=/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerratewz/${variable}/${cutoff}/merge1/
  for year in 20220 20221 20230 20231 20240 20250;
  do

     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M2",0.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M2",0.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M3",0.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M3",0.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M4",1.0, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M4",1.0, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M5",1.0, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M5",1.0, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T5",0.2, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T5",0.2, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T6",0.2, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T6",0.2, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T7",0.2, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T7",0.2, '"${cutoff}"', '"${variable}"')'

done
done
done


