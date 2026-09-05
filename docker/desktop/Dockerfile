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
    dbus-x11 \
    adwaita-icon-theme \
    firefox-esr \
    xclip \
    xdotool \
    x11-utils \
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

# Install kubectl v1.30.2
RUN curl -fsSL -o /usr/local/bin/kubectl https://dl.k8s.io/release/v1.30.2/bin/linux/amd64/kubectl && \
    chmod +x /usr/local/bin/kubectl

# Create candidate user exam
RUN useradd -u 1000 -m -s /bin/bash exam && \
    mkdir -p /home/exam/.vnc /home/exam/.kube /etc/firefox-esr/policies && \
    chown -R exam:exam /home/exam

# Configure exam user bashrc with CKA shortcuts & autocompletion
RUN echo "if [ -f /usr/share/bash-completion/bash_completion ]; then . /usr/share/bash-completion/bash_completion; fi" >> /home/exam/.bashrc && \
    echo "source <(kubectl completion bash 2>/dev/null) || true" >> /home/exam/.bashrc && \
    echo "alias k=kubectl" >> /home/exam/.bashrc && \
    echo "complete -o default -F __start_kubectl k 2>/dev/null || true" >> /home/exam/.bashrc && \
    echo 'export do="--dry-run=client -o yaml"' >> /home/exam/.bashrc && \
    echo 'export now="--force --grace-period=0"' >> /home/exam/.bashrc

# Install Firefox CKA policies and bookmarks
COPY policies.json /etc/firefox-esr/policies/policies.json

# Copy desk-agent and entrypoint
COPY desk-agent.py /usr/local/bin/desk-agent.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/desk-agent.py /usr/local/bin/entrypoint.sh

EXPOSE 5901 6080

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

