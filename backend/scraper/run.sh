for i in $(seq 1 15); do
    echo "=== Run $i/15 ==="
    RUN_NUMBER=$i TOTAL_RUNS=15 python3 main.py -l 100 || echo "Run $i failed, continuing..."
done