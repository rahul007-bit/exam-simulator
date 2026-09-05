kubectl create namespace auth-tokens --dry-run=client -o yaml | kubectl apply -f -
