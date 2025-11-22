#!/usr/bin/env bash

# Cài đặt các thư viện hệ thống cần thiết cho Pillow và các gói khác
apt-get update
apt-get install -y \
  libglib2.0-0 \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 \
  libffi-dev \
  shared-mime-info

# Cài đặt các thư viện Python
pip install -r requirements.txt
