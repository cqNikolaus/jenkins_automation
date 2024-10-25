FROM python

RUN apt-get update && \
    apt-get install -y --no-install-recommends dnsutils openssl git && \
    rm -rf /var/lib/apt/lists/*
    
WORKDIR /code

RUN git clone https://github.com/cqNikolaus/jenkins_automation.git /code

RUN pip install --no-cache-dir --upgrade -r requirements.txt

