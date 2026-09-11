FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8

# Install XFCE4 desktop, TigerVNC, noVNC, Firefox-ESR, Redis client, terminal, utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    tigervnc-standalone-server \
    tigervnc-tools \
    novnc \
    websockify \
    xfce4-session \
    xfwm4 \
    xfce4-panel \
    xfdesktop4 \
    xfce4-terminal \
    xfce4-notifyd \
    libnotify-bin \
    dbus-x11 \
    adwaita-icon-theme \
    firefox-esr \
    xclip \
    xdotool \
    xinput \
    x11-utils \
    x11-xserver-utils \
    python3 \
    python3-redis \
    procps \
    psmisc \
    curl \
    ca-certificates \
    bash-completion \
    vim \
    nano \
    jq \
    tmux \
    openssh-client \
    net-tools \
    iproute2 \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
COPY kubectl /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kubectl

# Create candidate user exam
RUN useradd -u 1000 -m -s /bin/bash exam && \
    mkdir -p /home/exam/.vnc /home/exam/.kube /etc/firefox-esr/policies && \
    chown -R exam:exam /home/exam

# Configure exam user bashrc with CKA shortcuts & autocompletion
RUN mkdir -p /etc/bash_completion.d && \
    /usr/local/bin/kubectl completion bash > /etc/bash_completion.d/kubectl 2>/dev/null || true && \
    echo "if [ -f /usr/share/bash-completion/bash_completion ]; then . /usr/share/bash-completion/bash_completion; fi" >> /home/exam/.bashrc && \
    echo "[ -f /etc/bash_completion.d/kubectl ] && . /etc/bash_completion.d/kubectl 2>/dev/null || true" >> /home/exam/.bashrc && \
    echo "alias k=kubectl" >> /home/exam/.bashrc && \
    echo "complete -o default -F __start_kubectl k 2>/dev/null || true" >> /home/exam/.bashrc && \
    echo 'export do="--dry-run=client -o yaml"' >> /home/exam/.bashrc && \
    echo 'export now="--force --grace-period=0"' >> /home/exam/.bashrc


# Install Firefox CKA policies and bookmarks
COPY policies.json /etc/firefox-esr/policies/policies.json
RUN mkdir -p /usr/lib/firefox-esr/distribution && \
    cp /etc/firefox-esr/policies/policies.json /usr/lib/firefox-esr/distribution/policies.json

# Copy desk-agent and entrypoint
COPY desk-agent.py /usr/local/bin/desk-agent.py
COPY desk-terminal-record.py /usr/local/bin/desk-terminal-record.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/desk-agent.py /usr/local/bin/desk-terminal-record.py /usr/local/bin/entrypoint.sh

EXPOSE 5901 6080

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

