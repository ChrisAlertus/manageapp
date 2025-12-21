#!/bin/bash
# Sync requirements.txt from pyproject.toml using uv
# This keeps requirements.txt in sync for compatibility

uv pip compile pyproject.toml -o requirements.txt

