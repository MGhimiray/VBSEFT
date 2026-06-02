#!/bin/sh
# to run: ./run_makeEFTDataCards.sh 1001 
if [ $# -lt 1 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

export theOption=$2
export theAna=sswwAnalysis$1

source /mnt/home/mghimiray/VBSStudies/cmsstyle/cmsstyle/scripts/setup_cmstyle

  input=/mnt/home/mghimiray/VBSStudies/Outputs_EFT/OriginalTT/1001/1000/merge1/

  for year in 20220 20221 20230 20231 20240 20250;
  do

     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M0",10.0)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M0",10.0)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M1",15.0)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M1",15.0)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M7",15.0)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M7",15.0)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"S0",15.0)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"S0",15.0)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T0",2.0)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T0",2.0)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T1",1.0)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T1",1.0)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T2",2.0)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T2",2.0)'

done


