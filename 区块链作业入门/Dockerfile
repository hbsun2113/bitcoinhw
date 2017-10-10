
# bitcoin container
FROM ubuntu:16.04
MAINTAINER ccen <mail2cchen^gmail^com>
RUN apt-get update -y && apt-get ins tall -y net-tools && apt-get install -y iproute && \
    mkdir -p ~/.bitcoin && echo "rpcuser=ccen\nrpcpassword=ccen" > ~/.bitcoin/bitcoin.conf

