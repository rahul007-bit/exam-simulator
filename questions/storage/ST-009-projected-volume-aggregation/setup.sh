kubectl create namespace app-credentials --dry-run=client -o yaml | kubectl apply -f -
