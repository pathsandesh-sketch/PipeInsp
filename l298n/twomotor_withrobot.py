import RPi.GPIO as GPIO
import time

# Motor A (Left)
IN1 = 17
IN2 = 27
ENA = 18

# Motor B (Right)
IN3 = 22
IN4 = 23
ENB = 13

GPIO.setmode(GPIO.BCM)

# Setup
GPIO.setup([IN1, IN2, IN3, IN4, ENA, ENB], GPIO.OUT)

# PWM setup
pwmA = GPIO.PWM(ENA, 1000)
pwmB = GPIO.PWM(ENB, 1000)

pwmA.start(70)  # speed %
pwmB.start(70)

def forward():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)

def backward():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)

def left():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)

def right():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)

def stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)

try:
    forward()
    time.sleep(3)

    left()
    time.sleep(2)

    right()
    time.sleep(2)

    backward()
    time.sleep(3)

    stop()

finally:
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()
