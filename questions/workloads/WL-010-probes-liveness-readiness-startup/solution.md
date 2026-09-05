# Solution for WL-010: Configure Liveness, Readiness, and Startup Probes

Create Pod `health-app` in `health-monitoring` with startupProbe (period 5s, failureThreshold 10), readinessProbe (httpGet /ready), and livenessProbe (httpGet /health).
