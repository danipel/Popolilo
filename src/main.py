#!/usr/bin/env python
# Entry Point Script
import uvicorn
from src.presentation.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
