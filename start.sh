#!/bin/bash

pkill -9 -f '/root/miniconda3/envs/photo/bin/python server.py'
pkill -9 -f '/root/miniconda3/envs/photo/bin/python -m celery'
# /root/miniconda3/envs/photo/bin/python server.py
/root/miniconda3/envs/photo/bin/python server.py > server.log 2>&1&
# /root/miniconda3/envs/photo/bin/python -m celery -A tasks flower --address='localhost'&