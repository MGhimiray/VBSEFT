dir=../../../../Outputs_EFT/fakerrate/1020/0000/datacards

for f in "$dir"/*sswwAnalysis1018_*; do
    mv "$f" "${f/sswwAnalysis1018/sswwAnalysis1020}"
done
