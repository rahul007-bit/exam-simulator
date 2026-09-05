# Solution for WL-013: Configure Pod Lifecycle preStop Hook

Create Pod `graceful-app` in `graceful-shutdown` with a `preStop` exec hook running `['/bin/sh', '-c', 'sleep 15; nginx -s quit']`.
