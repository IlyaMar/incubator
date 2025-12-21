#!/bin/bash

# Sandworm script - randomly selects and deletes pods matching a pattern
# Usage: ./sandworm.sh [pod-name-pattern] [deletion-probability] [namespace]
#   pod-name-pattern: Pattern to match pod names (default: "")
#   deletion-probability: Probability of deleting a pod (0.0-1.0, default: 0.3)
#   namespace: Kubernetes namespace (default: "default")

# Default values
POD_PATTERN="${1:-""}"
DELETE_PROBABILITY="${2:-0.3}"
NAMESPACE="${3:-default}"

# Log file
LOG_FILE="sandworm_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_message "ERROR: kubectl command not found. Please install kubectl."
        exit 1
    fi
}

# Function to get pods matching the pattern
get_matching_pods() {
    kubectl get pods -n "$NAMESPACE" --no-headers | grep "$POD_PATTERN" | awk '{print $1}'
}

# Function to randomly select pods for deletion
select_random_pods() {
    local pods=("$@")
    local selected_pods=()
    
    for pod in "${pods[@]}"; do
        # Generate random number between 0 and 1
        local random=$(awk -v min=0 -v max=1 'BEGIN{srand(); print min+rand()*(max-min)}')
        
        if (( $(echo "$random < $DELETE_PROBABILITY" | bc -l) )); then
            selected_pods+=("$pod")
        fi
    done
    
    echo "${selected_pods[@]}"
}

# Function to delete selected pods
delete_pods() {
    local pods=("$@")
    
    if [ ${#pods[@]} -eq 0 ]; then
        log_message "No pods selected for deletion this cycle."
        return
    fi
    
    for pod in "${pods[@]}"; do
        log_message "Deleting pod: $pod"
        kubectl delete pod "$pod" -n "$NAMESPACE"
        if [ $? -eq 0 ]; then
            log_message "Successfully deleted pod: $pod"
        else
            log_message "Failed to delete pod: $pod"
        fi
    done
}

# Main function
main() {
    log_message "Starting Sandworm with pattern: '$POD_PATTERN', probability: $DELETE_PROBABILITY, namespace: $NAMESPACE"
    check_kubectl
    
    # Infinite loop
    while true; do
        log_message "Scanning for pods matching pattern: '$POD_PATTERN'"
        
        # Get matching pods
        mapfile -t matching_pods < <(get_matching_pods)
        pod_count=${#matching_pods[@]}
        
        if [ $pod_count -eq 0 ]; then
            log_message "No pods found matching pattern: '$POD_PATTERN'"
        else
            log_message "Found $pod_count pods matching pattern"
            
            # Select random pods for deletion
            selected_pods=($(select_random_pods "${matching_pods[@]}"))
            selected_count=${#selected_pods[@]}
            
            log_message "Selected $selected_count/$pod_count pods for deletion"
            
            # Delete selected pods
            delete_pods "${selected_pods[@]}"
        fi
        
        log_message "Sleeping for 60 seconds before next cycle..."
        sleep 60
    done
}

# Trap Ctrl+C to exit gracefully
trap 'log_message "Sandworm terminated by user"; exit 0' INT

# Run the main function
main