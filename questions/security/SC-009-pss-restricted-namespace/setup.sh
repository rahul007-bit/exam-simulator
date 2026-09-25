kubectl create namespace secure-zone --dry-run=client -o yaml | kubectl apply -f -
