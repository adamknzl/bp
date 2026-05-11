#!/bin/bash
# @file   run.sh
# @brief  Executes the ETL pipeline in batches to populate the database.
#         Runs the pipeline N times, processing BATCH_SIZE organizations per
#         run. Already-processed organizations are skipped automatically.
# @usage  ./run.sh [total_runs] [batch_size]
#         ./run.sh          # defaults: 15 runs, 100 per batch
#         ./run.sh 30 50    # 30 runs, 50 per batch

set -euo pipefail

TOTAL_RUNS=${1:-15}
BATCH_SIZE=${2:-100}
FAILED_RUNS=0

echo "========================================="
echo " ETL Pipeline - batch execution"
echo " Runs:       $TOTAL_RUNS"
echo " Batch size: $BATCH_SIZE"
echo "========================================="
echo ""

for i in $(seq 1 "$TOTAL_RUNS"); do
    echo "--- Run $i / $TOTAL_RUNS ---"

    if RUN_NUMBER=$i TOTAL_RUNS=$TOTAL_RUNS python3 main.py -l "$BATCH_SIZE"; then
        echo "Run $i completed successfully."
    else
        FAILED_RUNS=$((FAILED_RUNS + 1))
        echo "WARNING: Run $i failed. Continuing..." >&2
    fi

    echo ""
done

echo "========================================="
echo " Pipeline execution finished."
echo " Successful runs: $((TOTAL_RUNS - FAILED_RUNS)) / $TOTAL_RUNS"
if [ "$FAILED_RUNS" -gt 0 ]; then
    echo " Failed runs:     $FAILED_RUNS"
fi
echo "========================================="