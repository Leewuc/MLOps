#!/bin/bash

sudo yum groupinstall -y "Development Tools"
sudo yum install -y openssl-devel

git clone https://github.com/wg/wrk.git
cd wrk
make
sudo cp wrk /usr/local/bin
