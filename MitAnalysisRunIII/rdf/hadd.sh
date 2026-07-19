#!/usr/bin/env bash
set -uo pipefail

year="${1:?Usage: $0 <2022|2023|2024|2025>}"

command -v hadd >/dev/null || {
  echo "ERROR: hadd not found in PATH"
  exit 1
}

# --------------------------------------------------
# Merge two files, or copy the only available file
# --------------------------------------------------
merge_or_copy()
{
  local in1="$1"
  local in2="$2"
  local out="$3"

  local has_in1=0
  local has_in2=0

  [[ -f "$in1" ]] && has_in1=1
  [[ -f "$in2" ]] && has_in2=1

  if (( has_in1 && has_in2 )); then

    echo "hadd -> $out"

    if ! hadd -f "$out" "$in1" "$in2"; then
      echo "ERROR: hadd failed for:"
      echo "  $in1"
      echo "  $in2"
      return 1
    fi

  elif (( has_in1 )); then

    echo "WARNING: missing file:"
    echo "  $in2"
    echo "Using only:"
    echo "  $in1"
    echo "Copying -> $out"

    cp -f "$in1" "$out"

  elif (( has_in2 )); then

    echo "WARNING: missing file:"
    echo "  $in1"
    echo "Using only:"
    echo "  $in2"
    echo "Copying -> $out"

    cp -f "$in2" "$out"

  else

    echo "WARNING: both input files are missing:"
    echo "  $in1"
    echo "  $in2"
    echo "No output produced:"
    echo "  $out"

  fi
}


for dir in 1000; do
  for cutoff in 0000; do

    echo "Processing directory $dir with cutoff $cutoff for year $year"

    inputdir="/mnt/home/mghimiray/VBSStudies/Outputs_EFT/matrix_method/${dir}/${cutoff}/histo/fillhisto_sswwAnalysis"
    outdir="/mnt/home/mghimiray/VBSStudies/Outputs_EFT/OriginalTT/${dir}/${cutoff}/histo/fillhisto_sswwAnalysis"

    mkdir -p "$outdir"

    for i in {0..14}; do

      echo "Processing job index $i for year $year"

      if [[ "$year" == "2023" ]]; then

        for sample in 1022 1032 1042; do
          in1="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year202301_job${i}.root"
          in2="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20230_job${i}.root"
          out="$outdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20230_job${i}.root"

          merge_or_copy "$in1" "$in2" "$out"
        done

        for sample in 1023 1033 1043; do
          in1="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year202311_job${i}.root"
          in2="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20231_job${i}.root"
          out="$outdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20231_job${i}.root"

          merge_or_copy "$in1" "$in2" "$out"
        done


      elif [[ "$year" == "2024" ]]; then

        for sample in \
          1022 1023 1024 1025 1026 1027 1028 \
          1032 1033 1034 1035 1036 1037 1038 \
          1042 1043 1044 1045 1046 1047 1048
        do
          in1="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year202401_job${i}.root"
          in2="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20240_job${i}.root"
          out="$outdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20240_job${i}.root"

          merge_or_copy "$in1" "$in2" "$out"
        done


      elif [[ "$year" == "2025" ]]; then

        for sample in \
          1021 1022 1023 1024 1025 1026 \
          1031 1032 1033 1034 1035 1036 \
          1041 1042 1043 1044 1045 1046
        do
          in1="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year202501_job${i}.root"
          in2="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20250_job${i}.root"
          out="$outdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20250_job${i}.root"

          merge_or_copy "$in1" "$in2" "$out"
        done


      elif [[ "$year" == "2022" ]]; then

        for sample in 1001 1002 1011 1012 1021 1022 1023 1031 1032 1033 1042 1043; do
          in1="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year202201_job${i}.root"
          in2="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20220_job${i}.root"
          out="$outdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20220_job${i}.root"

          merge_or_copy "$in1" "$in2" "$out"
        done

        for sample in 1024 1025 1026 1034 1035 1036 1044 1045 1046; do
          in1="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year202211_job${i}.root"
          in2="$inputdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20221_job${i}.root"
          out="$outdir/fillhisto_sswwAnalysis${dir}_sample${sample}_year20221_job${i}.root"

          merge_or_copy "$in1" "$in2" "$out"
        done


      else
        echo "ERROR: unsupported year: $year" >&2
        exit 2
      fi

    done
  done
done
