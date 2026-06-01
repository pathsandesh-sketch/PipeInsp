from flask import Flask, request
import RPi.GPIO as GPIO

app = Flask(__name__)

# Pin Definitions based on your layout (BCM Numbering)
IN1 = 17  # Left Motor Forward
IN2 = 27  # Left Motor Backward
IN3 = 22  # Right Motor Forward
IN4 = 23  # Right Motor Backward

GPIO.setmode(GPIO.BCM)
for pin in [IN1, IN2, IN3, IN4]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def stop_motors():
    for pin in [IN1, IN2, IN3, IN4]:
        GPIO.output(pin, GPIO.LOW)

@app.route('/motor', methods=['POST'])
def control_motor():
    command = request.form.get('direction')
    stop_motors() # Reset pins before applying next move
    
    if command == 'forward':
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
    elif command == 'backward':
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN4, GPIO.HIGH)
    elif command == 'left':
        # Spin left: Right motor forward, Left motor backward
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
    elif command == 'right':
        # Spin right: Left motor forward, Right motor backward
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN4, GPIO.HIGH)
    elif command == 'stop':
        stop_motors()
        
    return f"Motor set to {command}", 200

if __name__ == '__main__':
    # Listen on port 8000 on the Pi
    app.run(host='0.0.0.0', port=8000)
