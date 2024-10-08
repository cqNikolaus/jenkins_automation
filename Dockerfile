FROM python

RUN apt-get update && \
    apt-get install -y --no-install-recommends dnsutils openssl && \
    rm -rf /var/lib/apt/lists/*
    
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
