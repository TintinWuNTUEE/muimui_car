#!/usr/bin/python

from PCA9685 import PCA9685
import time
Dir = [
    'forward',
    'backward',
]
pwm = PCA9685(0x40, debug=True)
pwm.setPWMFreq(50)
class MotorDriver():
    def __init__(self):
        self.PWMA = 0
        self.AIN1 = 1
        self.AIN2 = 2
        self.PWMB = 5
        self.BIN1 = 3
        self.BIN2 = 4

    def MotorRun(self, motor, index, speed):
        if speed > 100:
            return
        if(motor == 0):
            pwm.setDutycycle(self.PWMA, speed)
            if(index == Dir[0]):
                pwm.setLevel(self.AIN1, 0)
                pwm.setLevel(self.AIN2, 1)
            else:
                pwm.setLevel(self.AIN1, 1)
                pwm.setLevel(self.AIN2, 0)
        else:
            pwm.setDutycycle(self.PWMB, speed)
            if(index == Dir[0]):
                pwm.setLevel(self.BIN1, 0)
                pwm.setLevel(self.BIN2, 1)
            else:
                pwm.setLevel(self.BIN1, 1)
                pwm.setLevel(self.BIN2, 0)

    def MotorStop(self, motor):
        if (motor == 0):
            pwm.setDutycycle(self.PWMA, 0)
        else:
            pwm.setDutycycle(self.PWMB, 0)

def ResetMotor(Motor):
    Motor.MotorStop(0)
    Motor.MotorStop(1)
    return


def MotorForward(Motor):
    Motor.MotorRun(0, 'forward', 100)
    Motor.MotorRun(1, 'backward', 100)
    return

def MotorLeftward(Motor):
    Motor.MotorRun(0, 'backward', 100)
    Motor.MotorRun(1, 'backward', 100)
    return

def MotorRightward(Motor):
    Motor.MotorRun(0, 'forward', 100)
    Motor.MotorRun(1, 'forward', 100)
    return

def MotorBackward(Motor):
    Motor.MotorRun(0, 'backward', 100)
    Motor.MotorRun(1, 'forward', 100)
    return

if __name__ == "__main__":
    print("----- test motor ----")
    motor = MotorDriver()
    motor.MotorRun(0, 'forward', 100)
    motor.MotorRun(1, 'backward', 100)
    time.sleep(1)
    motor.MotorStop(0)
    motor.MotorStop(1)
