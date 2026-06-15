#!/bin/sh
# to run: ./run_makeEFTDataCards.sh 1012 
if [ $# -lt 1 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

export theOption=$2
export theAna=sswwAnalysis$1

source /mnt/home/mghimiray/VBSStudies/cmsstyle/cmsstyle/scripts/setup_cmstyle

  input=/mnt/home/mghimiray/VBSStudies/Outputs_EFT/OriginalTT/1012/0000/merge1/

  for year in 20220 20221 20230 20231 20240 20250;
  do

     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M0",1.0)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M0",1.0)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M1",1.5)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M1",1.5)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"M7",1.5)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"M7",1.5)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"S0",1.5)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"S0",1.5)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T0",0.2)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T0",0.2)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T1",0.1)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T1",0.1)'
     root -l -q -b makeEFTDatacards.C'(0,0,"'${input}'","'${theAna}'",'"${year}"',"T2",0.2)'
     root -l -q -b makeEFTDatacards.C'(0,1,"'${input}'","'${theAna}'",'"${year}"',"T2",0.2)'

done


