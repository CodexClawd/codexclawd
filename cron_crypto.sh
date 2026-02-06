#!/bin/bash
# Cron wrapper for daily crypto ping

export BINANCE_API_KEY="${BINANCE_API_KEY:-}"
export BINANCE_SECRET_KEY="${BINANCE_SECRET_KEY:-}"

cd /home/boss/.openclaw/workspace/skills/binance
/home/boss/.openclaw/workspace/venv/bin/python3 daily_crypto_ping.py >> /tmp/crypto_cron.log 2>&1
