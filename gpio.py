

import RPi.GPIO as GPIO
import time
import subprocess
import dbus
from pins import *


def debounceRead(pin):
    while True:
        value1 = GPIO.input(pin)
        time.sleep(0.01)
        value2 = GPIO.input(pin)
        if value1 == value2:
            return value1    

#===========================================================

class ShutdownButton:
    def __init__(self, pin):
        GPIO.setup(pin, GPIO.IN)
        self.pin = pin
        self.initiated = False
        self.lastTime = 0
        self.downTime = 0

    def shutdown(self, time):
        print 'halt', time
        subprocess.call(["halt"])

    def reboot(self, time):
        print 'reboot', time
        subprocess.call(["reboot"])

    # time is in seconds
    def update(self, time):
        if self.lastTime == 0:
            self.lastTime = time
            return        
        value = debounceRead(self.pin)

        # accumulate downtime
        if value:
            self.downTime = self.downTime + (time  - self.lastTime)
        else:
            # if button is depressed, peform action depending on accumulated downtime
            if self.downTime > 3.0:
                self.shutdown(time)
            elif self.downTime > 0.5:
                self.reboot(time)
            # button depressed, reset downtime
            self.downTime = 0

        #print 'ButtonShutdown', value
        self.lastTime = time


#============================================================

class PvrQuery:
    def opensocket(self):
        import socket
        host = '192.168.0.10'
        port = 5556
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
    def closesocket(self):
        self.socket.close()
    def start(self):
        try:
            self.opensocket()
            self.socket.send('START')
            self.socket.recv(1024)
            self.closesocket()
        except:
            None
    def stop(self):
        try:
            self.opensocket()
            self.socket.send('STOP')
            self.socket.recv(1024)
            self.closesocket()
        except:
            None
    def check(self):
        try:
            self.opensocket()
            self.socket.send('STATUS')
            response = self.socket.recv(1024)
            self.closesocket()
            return response
        except:
            return ''


class PvrRecordIndicator:
    def __init__(self, pin):
        GPIO.setup(pin, GPIO.OUT)
        #try:
        self.pvrquery = PvrQuery()
        #except:
        #    self.pvrquery = None
        self.pin = pin
        self.record = False
        self.standby = False
        self.timeLastCheckRecord = 0
        self.indicatorFlashOn = False
        self.timeLastIndicatorFlashUpdate = 0
        self.indicatorFlashPeriod  = 0.1
    def updateRecord(self, time):
        #print time, self.timeLastCheckRecord
        if time - self.timeLastCheckRecord > 1.0:
            if self.pvrquery:
                response = self.pvrquery.check()
                self.record = response == 'RECORDING'
                self.standby = response == 'STANDBY'
            else:
                self.record = False
                self.standby = False
            self.timeLastCheckRecord = time
    def updateIndicatorFlash(self, time):
        if self.record:
            if time - self.timeLastIndicatorFlashUpdate > self.indicatorFlashPeriod:
                self.indicatorFlashOn = not self.indicatorFlashOn 
                self.timeLastIndicatorFlashUpdate = time
        elif self.standby:
            self.indicatorFlashOn = True
        else:
            self.indicatorFlashOn = False
    # time is in seconds
    def update(self, time):
        self.updateRecord(time)
        self.updateIndicatorFlash(time)
        #print 'pvrRecordIndicator', self.indicatorFlashOn
        GPIO.output(self.pin, self.indicatorFlashOn)


class ActionButton:
    def __init__(self, pin, action):
        GPIO.setup(pin, GPIO.IN)
        self.pin = pin
        self.action = action

    # time is in seconds
    def update(self, t):
        value = debounceRead(self.pin)
        if value:
            self.action()
            time.sleep(1)


def TogglePvrRecordingState():
    pvr = PvrQuery()
    if pvr:
        response = pvr.check()
        if response == 'RECORDING' or response == 'STANDBY':
            pvr.stop()
        elif response == 'STOPPED':
            pvr.start()

class LedTest:
    def __init__(self, pins_list):
        self.pins_list = pins_list
        for pin in pins_list:
            GPIO.setup(pin, GPIO.OUT)
    def update(self, t):
        for pin in self.pins_list:
            GPIO.output(pin, True)
            time.sleep(0.5)
            GPIO.output(pin, False)

def main():
    # use P1 header pin numbering convention
    GPIO.setmode(GPIO.BOARD)
    waitPeriod = 0.01
    shutdownButton = ShutdownButton(PIN_POWER_BUTTON)
    recordButton = ActionButton(PIN_RECORD_BUTTON, TogglePvrRecordingState)
    pvrRecordIndicator = PvrRecordIndicator(PIN_RECORDING_LED)
#    ledTest = LedTest([PIN_RECORDING_LED, PIN_LED2, PIN_LED3])
    t0 = time.time()
    while True:
        t = time.time() - t0
        shutdownButton.update(t)
        recordButton.update(t)
        pvrRecordIndicator.update(t)
#        ledTest.update(t)
        time.sleep(waitPeriod)
        
if __name__ == "__main__":
    main()
