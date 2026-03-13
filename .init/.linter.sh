#!/bin/bash
cd /home/kavia/workspace/code-generation/bus-booking-system-243652-243666/bus_app_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

