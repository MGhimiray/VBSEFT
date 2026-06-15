#!/usr/bin/env bash
# Usage: ./checkfiles.sh <year> <whichana>
# Example: ./checkfiles.sh 2022 1001
# Optional: DRYRUN=1 ./checkfiles.sh 2024 1001

set -uo pipefail

year=${1:?Usage: $0 YEAR WHICHANA}
whichana=${2:?Usage: $0 YEAR WHICHANA}

# Output directory
outdir="/mnt/home/mghimiray/VBSStudies/Outputs_EFT/Fakerate/output/"

echo "== Check files =="
echo " year     : $year"
echo " whichana : $whichana"
echo " outdir   : $outdir"
echo

if [[ ! -d "$outdir" ]]; then
  echo "ERROR: Output dir not found: $outdir"
  exit 2
fi

# Jobs expected
which_job="0 1 2 3 4 5 6 7 8 9"

# Map of <yearTag> -> <process list>
declare -A year_process_map
declare -a tags

if [[ "$year" == "2022" ]]; then
  tags=(20220 20221)
  year_process_map["20220"]="100 101 108 109 111 112 113 1011 1012 1031 1032 1033 1042 1043"
  year_process_map["20221"]="200 201 208 209 211 212 213 1034 1035 1036 1044 1045 1046"

elif [[ "$year" == "2023" ]]; then
  tags=(20230 20231)
  year_process_map["20230"]="300 301 308 309 311 312 313 1032 1042"
  year_process_map["20231"]="400 401 408 409 411 412 413 1033 1043"

elif [[ "$year" == "2024" ]]; then
  tags=(20240)
  year_process_map["20240"]="500 501 508 509 511 512 513 525 526 527 528 542 543 1032 1033 1034 1035 1036 1037 1038 1042 1043 1044 1045 1046 1047 1048"

elif [[ "$year" == "2025" ]]; then
  tags=(20250)
  year_process_map["20250"]="500 501 508 509 511 512 513 525 526 527 528 542 543 1031 1032 1033 1034 1035 1036 1041 1042 1043 1044 1045 1046"

else
  echo "Unsupported year: $year"
  exit 3
fi

# Helper: find highest completed job index for a given (tag, process)
# Returns -1 if none found
get_max_seen_job() {
  local tag="$1"
  local process="$2"

  shopt -s nullglob
  local arr=( "$outdir"/fillhisto_sswwAnalysis"${whichana}"_sample"${process}"_year"${tag}"1_job*.root )
  shopt -u nullglob

  local max=-1
  local f
  for f in "${arr[@]}"; do
    if [[ "$f" =~ _job([0-9]+)\.root$ ]]; then
      local j="${BASH_REMATCH[1]}"
      (( j > max )) && max="$j"
    fi
  done
  echo "$max"
}

missing_detail=()        # rows: "year whichana tag process job path"
declare -A missing_pairs # keys: "tag process"

total_expected=0
total_found=0


for tag in "${tags[@]}"; do
  for process in ${year_process_map[$tag]}; do
    for job in $which_job; do
      f="$outdir/fillhisto_fakeAnalysis_sample${process}_year${tag}_job${job}.root"
      (( total_expected++ ))

      if [[ -s "$f" ]]; then
        (( total_found++ ))
      else
        echo "MISSING: $f"
        missing_detail+=("$year $whichana $tag $process $job $f")
        missing_pairs["$tag $process"]=1
      fi
    done
  done
done

echo
echo "== Summary =="
echo " Found $total_found / $total_expected files in:"
echo "   $outdir"

if ((${#missing_detail[@]})); then
  echo
  echo " -- Missing files (detailed) --"
  printf "year whichana tag process job path\n"
  printf "%s\n" "${missing_detail[@]}"

  echo
  echo " -- Missing (yearTag, process) pairs --"
  for k in "${!missing_pairs[@]}"; do
    printf "%s\n" "$k"
  done | sort -V

  echo
  echo " -- Resubmitting missing jobs --"
  declare -A submitted
  mkdir -p log

  while read -r y wa tag process job path; do
    key="$tag $process $job"
    [[ -n "${submitted[$key]:-}" ]] && continue
    submitted["$key"]=1

    max_seen=$(get_max_seen_job "$tag" "$process")
    if (( max_seen >= 0 && job > max_seen )); then
      echo "skip: $tag $process job $job (likely no input group; max seen job index is $max_seen)"
      continue
    fi

    echo "./submit_cis_fake.sh $tag $process $job"
    if [[ -z "${DRYRUN:-}" ]]; then
      sbatch -p INTEL_HASWELL --time=70:00:00 --cpus-per-task=1 --nodes=1 \
        --job-name="vbsfake_${year}_${process}_${job}" \
        --output="log/vbsfake__${year}_${process}_${job}.out" \
        --error="log/vbsfake__${year}_${process}_${job}.err" \
        submit_cis_fake.sh "$tag" "$process" "$job" \
        || echo "  (warn) submit failed for $tag $process $job"
    fi
  done < <(printf "%s\n" "${missing_detail[@]}")

  exit 1
else
  echo " All expected files are present."
fi
