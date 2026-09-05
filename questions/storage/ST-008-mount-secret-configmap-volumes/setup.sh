kubectl create namespace app-configs --dry-run=client -o yaml | kubectl apply -f -
