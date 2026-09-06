kubectl create namespace batch-schedules --dry-run=client -o yaml | kubectl apply -f -
