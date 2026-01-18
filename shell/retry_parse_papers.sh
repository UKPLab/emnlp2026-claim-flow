#!/usr/bin/env bash

while true; do

    uv run hypoflow/process_papers_docling.py
    status=$?

    if [ $status -eq 0 ]; then
        echo "Process completed successfully."
        break
    # else
    #     echo "Process failed with status $status. Retrying in 10 seconds..."
    #     sleep 10
    fi


    echo "Process failed with status $status. Retrying in 10 seconds..."
    sleep 10

done