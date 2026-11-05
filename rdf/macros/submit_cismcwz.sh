#!/bin/bash

# Usage:
# ./submit_cis.sh year variable
# year = 2022, 2023, 2024, 2025, or 2027
# 2027 processes all years

whichyear=$1
variable=$2
makedataCards=$((variable - 1000))

declare -A year_process_map

which_job="0 1 2 3"

if [ "$whichyear" = "2027" ]; then

    # Process all years
    year_process_map["20220"]="179 183 114 115 116 117 118 119 120 121 122 123 124 129 130 131 132 139 140 141 144 148 149 155 159 160 161 162 163 164 178 182 190 "
    year_process_map["20221"]="279 283 214 215 216 217 218 219 220 221 222 223 224 229 230 231 232 239 240 241 244 248 249 255 259 260 261 262 263 264 278 282 290 "
    year_process_map["20230"]="379 383 314 315 316 317 318 319 320 321 322 323 324 329 330 331 332 344 348 349 355 359 360 361 362 363 364 378 382 390"
    year_process_map["20231"]="479 483 414 415 416 417 418 419 420 421 422 423 424 429 430 431 432 444 448 449 455 459 460 461 462 463 464 478 482 490"
    year_process_map["20240"]="579 583 514 515 516 517 518 519 520 521 522 523 524 529 532 539 548 549 555 559 560 561 562 563 564 578 582 586 587 588 590"
    year_process_map["20250"]="679 683 614 615 616 617 618 619 620 621 622 623 624 629 632 639 648 649 655 659 660 661 662 663 664 678 682 686 687 688 690"

elif [ "$whichyear" = "2023" ]; then

    year_process_map["20230"]="379 383 314 315 316 317 318 319 320 321 322 323 324 329 330 331 332 344 348 349 355 359 360 361 362 363 364 378 382 390"
    year_process_map["20231"]="479 483 414 415 416 417 418 419 420 421 422 423 424 429 430 431 432 444 448 449 455 459 460 461 462 463 464 478 482 490"
    
elif [ "$whichyear" = "2024" ]; then

    year_process_map["20240"]="579 583 514 515 516 517 518 519 520 521 522 523 524 529 532 539 548 549 555 559 560 561 562 563 564 578 582 586 587 588 590"
    
elif [ "$whichyear" = "2022" ]; then

    year_process_map["20220"]="179 183 114 115 116 117 118 119 120 121 122 123 124 129 130 131 132 139 140 141 144 148 149 155 159 160 161 162 163 164 178 182 190 "
    year_process_map["20221"]="279 283 214 215 216 217 218 219 220 221 222 223 224 229 230 231 232 239 240 241 244 248 249 255 259 260 261 262 263 264 278 282 290 "
   
elif [ "$whichyear" = "2025" ]; then

    year_process_map["20250"]="679 683 614 615 616 617 618 619 620 621 622 623 624 629 632 639 648 649 655 659 660 661 662 663 664 678 682 686 687 688 690"

else
    echo "Invalid year: $whichyear"
    echo "Allowed values: 2022, 2023, 2024, 2025, 2027"
    exit 1
fi

cutoff="0000"

mkdir -p log

for year in "${!year_process_map[@]}"; do
    echo "Year: $year"

    processes="${year_process_map[$year]}"

    for process in $processes; do
        for jobs in $which_job; do


            echo "Submitting: Year=$year, Process=$process, Job=$jobs, Cutoff=$cutoff, MakeDataCards=$makedataCards"

            sbatch -p INTEL_HASWELL \
                --time=70:00:00 \
                --cpus-per-task=1 \
                --nodes=1 \
                --job-name="${makedataCards}wz_OriginalTT_${year}_${process}_${jobs}" \
                --output="log/vbsmcwz_${year}_${process}_${jobs}.out" \
                --error="log/vbsmcwz_${year}_${process}_${jobs}.err" \
                submit_cis_analysis.sh \
                "$year" \
                "$process" \
                "$jobs" \
                "$cutoff" \
                "$makedataCards"
        done
    done
done


