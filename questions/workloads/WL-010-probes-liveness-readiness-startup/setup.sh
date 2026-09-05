kubectl create namespace health-monitoring --dry-run=client -o yaml | kubectl apply -f -
