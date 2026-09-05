kubectl create namespace web-application --dry-run=client -o yaml | kubectl apply -f -
