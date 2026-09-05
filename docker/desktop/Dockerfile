FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8

# Install X11, Openbox, TigerVNC, noVNC, Firefox-ESR, Redis client and X utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    tigervnc-standalone-server \
    tigervnc-tools \
    novnc \
    websockify \
    openbox \
    firefox-esr \
    xclip \
    xdotool \
    x11-utils \
    python3 \
    python3-redis \
    procps \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create candidate user exam
RUN useradd -u 1000 -m -s /bin/bash exam && \
    mkdir -p /home/exam/.vnc /etc/firefox-esr/policies && \
    chown -R exam:exam /home/exam

# Install Firefox CKA policies and bookmarks
COPY policies.json /etc/firefox-esr/policies/policies.json

# Copy desk-agent and entrypoint
COPY desk-agent.py /usr/local/bin/desk-agent.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/desk-agent.py /usr/local/bin/entrypoint.sh

EXPOSE 5901 6080

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
