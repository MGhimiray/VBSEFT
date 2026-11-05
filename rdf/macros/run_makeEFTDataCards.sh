#!/bin/sh
# to run: ./run_makeEFTDataCards.sh 1012 

export theOption=$2
#export theAna=sswwAnalysis$1
#export variable=$1

source /mnt/home/mghimiray/VBSStudies/cmsstyle/cmsstyle/scripts/setup_cmstyle
 
  for variable in 1010 1013 1014 1022 1023 1016;do
  theAna=sswwAnalysis$variable
  for cutoff in 0000 1000 1200 1500 2000 3000;
  do
  input=/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/${variable}/${cutoff}/merge1/
  for year in 20220 20221 20230 20231 20240 20250;
  do

     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M0",1.0, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M0",1.0, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M1",1.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M1",1.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M7",1.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M7",1.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"S0",1.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"S0",1.5, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T0",0.2, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T0",0.2, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T1",0.1, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T1",0.1, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T2",0.2, '"${cutoff}"', '"${variable}"')'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T2",0.2, '"${cutoff}"', '"${variable}"')'

done
done
done


