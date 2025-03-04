FROM python:3.11

# Download precompiled ttyd binary from GitHub releases
RUN apt-get update && \
    apt-get install -y wget && \
    wget https://github.com/tsl0922/ttyd/releases/download/1.6.3/ttyd.x86_64 -O /usr/bin/ttyd && \
    chmod +x /usr/bin/ttyd && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ENV NVM_DIR /root/.nvm

COPY install.sh /tmp/install.sh
RUN bash /tmp/install.sh \
    && . "$NVM_DIR/nvm.sh" \
    && nvm install node \
    && nvm use node

WORKDIR /usr/src/app
COPY . .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
RUN python -m venv pilot-env
RUN /bin/bash -c "source pilot-env/bin/activate"

RUN pip install -r requirements.txt
WORKDIR /usr/src/app/pilot

EXPOSE 7681
CMD ["ttyd", "bash"]
