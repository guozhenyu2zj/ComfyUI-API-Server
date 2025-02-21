#!/bin/bash

pkill -9 -f '/root/miniconda3/envs/photo/bin/python server.py'
# pkill -9 -f '/root/miniconda3/envs/photo/bin/python -m celery'
# /root/miniconda3/envs/photo/bin/python server.py
/root/miniconda3/envs/photo/bin/python server.py > /dev/null &
# /root/miniconda3/envs/photo/bin/python -m celery -A tasks flower --address='localhost'&
