#!/usr/bin/env python
from flask import Flask, render_template, Response, flash, jsonify
from flask_socketio import SocketIO
from camera import Camera
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import time 

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'well-secret-password'
bootstrap = Bootstrap(app)
socketio = SocketIO(app)
camera = Camera()
    
class MyForm(FlaskForm):
    nomask = SubmitField(label='NoMask')
    green = SubmitField(label='Green')
    yellow = SubmitField(label='Yellow')
 
@app.route('/',  methods=['GET', 'POST']) 
def index():
    form = MyForm()
    if form.validate_on_submit():
        if form.nomask.data:
            flash("You pressed nomask button")
            camera.removemask()
        elif form.green.data:
            flash("You pressed green button")
            camera.setmaskgreen()        
        elif form.yellow.data:
            flash("You pressed yellow button")
            camera.setmaskyellow()
    return render_template('index.html', form=form)
		
def gen(camera):
    """Video streaming generator function."""
    count = 0
    currentvalue = False
    socketio.emit('my_response', {'mse' : 'No Bee detected'})
    while True:
        frame = camera.get_frame()       
        if camera.mse > 0 and currentvalue == False:        
            socketio.emit('my_response', {'mse' : 'Bee detected', 'elapsed' : 0})
            start_time = time.time()
            currentvalue = True
        elif camera.mse == 0 and currentvalue == True:        
            elapsed_time = time.time() - start_time
            socketio.emit('my_response', {'mse' : 'No Bee detected', 'elapsed' : elapsed_time})
            currentvalue = False                    
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
        return Response(gen(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame') 

@app.route('/detection')
def detection():
    return jsonify(result=camera.mse);
    
@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    return 'one', 2    

@socketio.on('message')
def handle_message(message):
    print('socketio', message)
    send(message)
    
if __name__ == '__main__':
    #app.run(host='0.0.0.0', debug=True, threaded=True)
    socketio.run(app, host='0.0.0.0', debug=True)
