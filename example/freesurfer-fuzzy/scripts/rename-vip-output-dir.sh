#!/bin/bash

# Initialize a counter
counter=1

# Loop through all items in the current directory
for dir in */; do
    # Check if the item is a directory
    if [ -d "$dir" ]; then
        # Rename the directory using the counter value
        mv -- "$dir" "rep$counter"
        # Increment the counter
        ((counter++))
    fi
done

echo "Directories have been renamed."
