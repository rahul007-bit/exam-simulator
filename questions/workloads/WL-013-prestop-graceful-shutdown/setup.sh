kubectl create namespace graceful-shutdown --dry-run=client -o yaml | kubectl apply -f -
