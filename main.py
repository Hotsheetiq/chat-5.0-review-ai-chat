# Import proper Twilio Media Streams app with Flask-Sockets
from twilio_media_streams_app import create_app
import os

# Create app with correct Twilio Media Streams protocol (Flask-Sockets)
app, sockets = create_app()

# Run with gevent WebSocket server when executed directly
if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    PORT = int(os.environ.get('PORT', 5000))
    server = pywsgi.WSGIServer(('0.0.0.0', PORT), app, handler_class=WebSocketHandler)
    server.serve_forever()