"""Versión sin ventana de consola — se ejecuta en segundo plano."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app import app
app.run(port=5055, debug=False)
