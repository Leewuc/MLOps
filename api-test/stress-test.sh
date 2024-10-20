#!/bin/bash

wrk \
  -t 2 \ 
  -c 5 \
  -d 30s \
  --latency \
  -H "x-api-key <API_KEY>" \
  <API_ENDPOINT>/like/movie?user=0
