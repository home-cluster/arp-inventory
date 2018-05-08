FROM alpine:latest

RUN apk update && apk add net-tools python3 py3-ipaddress

COPY inventory.py /usr/local/bin/inventory.py

ENTRYPOINT ["/usr/local/bin/inventory.py"]
