"""
Application entry point
"""
import os
from app import create_app

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Development server configuration
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 70)
    print("Weather Data Management System")
    print("Indian Meteorological Department - Chennai")
    print("=" * 70)
    print(f"Server running on: http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print("Press CTRL+C to quit")
    print("=" * 70)
    print()
    
    app.run(host=host, port=port, debug=debug)
