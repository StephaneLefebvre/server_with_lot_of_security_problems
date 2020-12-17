#! -*- enconding: utf-8 -*-
# From https://dev.to/raymag/building-a-simple-webchat-2504

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static/')
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('client_message')
def receive_message (client_msg):
    emit('server_message', client_msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)

