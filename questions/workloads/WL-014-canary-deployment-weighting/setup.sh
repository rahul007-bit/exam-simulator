kubectl create namespace traffic-canary --dry-run=client -o yaml | kubectl apply -f -
