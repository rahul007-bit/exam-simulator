kubectl create namespace default --dry-run=client -o yaml | kubectl apply -f -
