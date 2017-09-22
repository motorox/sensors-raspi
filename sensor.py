#!/usr/bin/env python
#
# Kept the following copyright info, because i used parts of the code made by Michael.
#
# Michael Saunby. April 2013
#
# Notes.
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#
#   Copyright 2013 Michael Saunby
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import pexpect
import sys
import time
import json
import select
import logging
import threading

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
    return t

# This algorithm borrowed from
# http://processors.wiki.ti.com/index.php/SensorTag_User_Guide#Gatt_Server
# which most likely took it from the datasheet.  I've not checked it, other
# than noted that the temperature values I got seemed reasonable.
#
#   Copyright 2013 Michael Saunby
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

tag = None
tosigned = lambda n: float(n-0x10000) if n > 0x7fff else float(n)
tosignedbyte = lambda n: float(n-0x100) if n > 0x7f else float(n)

def calcTmpTarget(objT, ambT):
    objT = tosigned(objT)
    ambT = tosigned(ambT)

    m_tmpAmb = ambT/128.0
    Vobj2 = objT * 0.00000015625
    Tdie2 = m_tmpAmb + 273.15
    S0 = 6.4E-14            # Calibration factor
    a1 = 1.75E-3
    a2 = -1.678E-5
    b0 = -2.94E-5
    b1 = -5.7E-7
    b2 = 4.63E-9
    c2 = 13.4
    Tref = 298.15
    S = S0*(1+a1*(Tdie2 - Tref)+a2*pow((Tdie2 - Tref), 2))
    Vos = b0 + b1*(Tdie2 - Tref) + b2*pow((Tdie2 - Tref), 2)
    fObj = (Vobj2 - Vos) + c2*pow((Vobj2 - Vos), 2)
    tObj = pow(pow(Tdie2, 4) + (fObj/S), .25)
    tObj = (tObj - 273.15)
    return tObj

#
# Again from http://processors.wiki.ti.com/index.php/SensorTag_User_Guide#Gatt_Server
#
def calcHum(rawT, rawH):
    # -- calculate temperature [deg C] --
    t = -46.85 + 175.72/65536.0 * rawT

    rawH = float(int(rawH) & ~0x0003) # clear bits [1..0] (status bits)
    # -- calculate relative humidity [%RH] --
    rh = -6.0 + 125.0/65536.0 * rawH # RH= -6 + 125 * SRH/2^16
    return (t, rh)


#
# Again from http://processors.wiki.ti.com/index.php/SensorTag_User_Guide#Gatt_Server
# but combining all three values and giving magnitude.
# Magnitude tells us if we are at rest, falling, etc.

def calcAccel(rawX, rawY, rawZ):
    accel = lambda v: tosignedbyte(v) / 64.0  # Range -2G, +2G
    xyz = [accel(rawX), accel(rawY), accel(rawZ)]
    mag = (xyz[0]**2 + xyz[1]**2 + xyz[2]**2)**0.5
    return (xyz, mag)


#
# Again from http://processors.wiki.ti.com/index.php/SensorTag_User_Guide#Gatt_Server
# but combining all three values.
def calcMagn(rawX, rawY, rawZ):
    magforce = lambda v: (tosigned(v) * 1.0) / (65536.0/2000.0)
    return [magforce(rawX), magforce(rawY), magforce(rawZ)]

def calcGyro(rawX, rawY, rawZ):
    '''
    Taken from processors.wiki.ti.com/index.php/SensorTag_User_Guide
    calculate rotation, unit deg/s, range -250, +250
    '''
    f = lambda v: (tosigned(v) * 1.0) / (65536.0/500.0)
    return [f(rawX), f(rawY), f(rawZ)]

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s',)
class SensorTag(object):
    '''SensorTag class provides connects to a sensor, reads and writes data'''
    notificationLoop = False
    callbacks = None
    def __init__(self):
        # if bluetooth_adr <> "":
        #     self.con = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
        # else:
        self.con = pexpect.spawn('gatttool --interactive')
        self.con.expect('\[LE\]>', timeout=600)
    def connect(self, bluetooth_adr, callbacksClass):
        logging.debug("Preparing to connect. You might need to press the side button...")
        try:
            self.con.sendline('connect ' + bluetooth_adr)
            # test for success of connect
            self.con.expect('Connection successful.*\[LE\]>')
            # Earlier versions of gatttool returned a different message.  Use this pattern -
            #self.con.expect('\[CON\].*>')
            self.cb = {}

            #initialize the callbacks
            print "[re]starting.."

            cbs = callbacksClass(bluetooth_adr)

            # enable IR-Temperature sensor
            self.register_cb(0x21, cbs.tmp007)
            self.char_write_cmd(0x24, 0x01)
            self.char_write_cmd(0x22, 0x0100)

            # enable movement
            self.register_cb(0x39, cbs.movement)
            self.char_write_string(0x3c, 'ff:01')
            self.char_write_cmd(0x3a, 0x0100)

            # enable humidity
            self.register_cb(0x29, cbs.humidity)
            self.char_write_cmd(0x2c, 0x01)
            self.char_write_cmd(0x2a, 0x0100)

            # enable luxometer
            self.register_cb(0x41, cbs.lux)
            self.char_write_cmd(0x44, 0x01)
            self.char_write_cmd(0x42, 0x0100)

            # enable barometer
            self.register_cb(0x31, cbs.baro)
            self.char_write_cmd(0x34, 0x01)
            self.char_write_cmd(0x32, 0x0100)

            # enable keys
            self.register_cb(0x49, cbs.keys)
            self.char_write_cmd(0x4a, 0x0100)
            self.callbacks = cbs

            #start the notification thread automagically
            self.start_notification_thread()
        except Exception, e:
            print str(e)
            pass

        return

    def char_write_cmd(self, handle, value):
        # The 0%x for value is VERY naughty!  Fix this!
        cmd = 'char-write-cmd 0x%02x 0%x' % (handle, value)
        #print cmd
        self.con.sendline(cmd)
        return

    def char_write_string(self, handle, value):
        # The 0%x for value is VERY naughty!  Fix this!
        cmd = 'char-write-cmd 0x%02x %s' % (handle, value)
        #print cmd
        self.con.sendline(cmd)
        return

    def char_read_hnd(self, handle):
        self.con.sendline('char-read-hnd 0x%02x' % handle)
        self.con.expect('descriptor: .*? \r')
        after = self.con.after
        rval = after.split()[1:]
        return [long(float.fromhex(n)) for n in rval]

    # Notification handle = 0x0025 value: 9b ff 54 07
    def notification_loop(self):
        self.notificationLoop = True
        while self.notificationLoop:
            try:
                pnum = self.con.expect('Notification handle = .*? \r', timeout=4)
            except pexpect.TIMEOUT:
                print "TIMEOUT exception!"
                print(str(self.con))
                break
            if pnum==0:
                after = self.con.after
                hxstr = after.split()[3:]
                handle = long(float.fromhex(hxstr[0]))
                try:
                    self.cb[handle]([long(float.fromhex(n)) for n in hxstr[2:]])
                except:
                    print "Error in callback for %x" % handle
                    print sys.argv[1]
                pass
            else:
                print "TIMEOUT!!"
        print('notification loop ENDED !!!')

    def read_data(self, handle):
        val = self.char_read_hnd(handle)
        print val
        try:
            self.cb[handle](val)
        except:
            print "Error in callback for %x" % handle
            print sys.argv[1]
            pass

    def register_cb(self, handle, fn):
        self.cb[handle] = fn
        return

    def get_data(self):
        resp = ""
        if self.callbacks <> None:
            resp = json.dumps(self.callbacks.data)
        else:
            pass
        return resp
    def start_notification_thread(self):
        self.notThread = threading.Thread(target=self.notification_loop, name="Notification Thread")
        self.notThread.start()
    def disconnect(self):
        self.notificationLoop = False
        # print('Threads alive: ', threading.activeCount())
        # print('notif thread is alive: ', self.notThread.isAlive())
        mainThread = threading.currentThread()
        for t in threading.enumerate():
            if t is mainThread:
                continue
            logging.debug('joining %s', t.getName())
            logging.debug('thread %s is alive: %s', t.getName(), t.isAlive())
            t.join()
        self.con.sendline('disconnect')
    def quit(self):
        if self.notificationLoop == True:
            self.disconnect()
        self.con.sendline('quit')


class SensorCallbacks:

    data = {}

    def __init__(self, addr):
        self.data['addr'] = addr
        self.data['keys'] = 0

    def tmp007(self, v):
        objT = (v[1]<<8)+v[0]
        ambT = (v[3]<<8)+v[2]
        #print 'ObjT: ', objT
        #print 'Ambient: ', ambT/128.0
        self.data['ambtemp'] = ambT/128.0
        targetT = calcTmpTarget(objT, ambT)
        self.data['temp'] = targetT
        celsiusVal = (targetT - 32)*5.0/9.0 #FAHR to Celsius
        self.data['celsiustemp'] = celsiusVal
        #print "T007 %.1f" % celsiusVal

    def lux(self, v):
        lux = (v[1]<<8)+v[0]
        self.data['lux'] = lux
        #print 'Lux', lux

    def keys(self, v):
        keys = v[0]
        self.data['keys'] = keys
        #print 'Keys', keys

    def humidity(self, v):
        rawT = (v[1]<<8)+v[0]
        rawH = (v[3]<<8)+v[2]
        (t, rh) = calcHum(rawT, rawH)
        self.data['humdtemp'] = t
        self.data['humd'] = rh
        #print "HUMD %.1f" % rh
        #print "TEMP %.1f" % t

    def baro(self, v):
        rawT = ((v[2]<<16) + (v[1]<<8)+v[0])/100.0 # in Celsius
        rawP = ((v[5]<<16) + (v[4]<<8)+v[3])/100.0 # in hPa
        self.data['barotemp'] = rawT
        self.data['baropress'] = rawP
        #print "BARO", self.data['baro']
        self.data['time'] = long(time.time() * 1000)

    def movement(self, v):
        # enable magnetometer
        mx = (v[13]<<8)+v[12]
        my = (v[15]<<8)+v[14]
        mz = (v[17]<<8)+v[16]
        (mgnx, mgny, mgnz) = calcMagn(mx, my, mz)
        self.data['magnx'] = mgnx
        self.data['magny'] = mgny
        self.data['magnz'] = mgnz
        #print "MAGN", mxyz
        # enable accelerometer
        ax = (v[7]<<8)+v[6]
        ay = (v[9]<<8)+v[8]
        az = (v[11]<<8)+v[10]
        (axyz, mag) = calcAccel(ax, ay, az)
        self.data['accelx'] = axyz[0]
        self.data['accely'] = axyz[1]
        self.data['accelz'] = axyz[2]
        #print "ACCL", axyz
        #print "ACCL-mag", mag
        # enable gyroscope
        gx = (v[1]<<8)+v[0]
        gy = (v[3]<<8)+v[2]
        gz = (v[5]<<8)+v[4]
        gxyz = calcGyro(gx, gy, gz)
        self.data['gyrox'] = gxyz[0]
        self.data['gyroy'] = gxyz[1]
        self.data['gyroz'] = gxyz[2]
        #print "GYRO", gxyz


if __name__ == "__main__":
    print 'Testing sensor class'
    if len(sys.argv) < 2:
        sys.exit(1)
    else:
        st = SensorTag()
        st.connect(sys.argv[1], SensorCallbacks)
        st.start_notification_thread()
        while True:
            try:
                print st.get_data()
                time.sleep(10)
            except KeyboardInterrupt, e:
                print str(e)
                break
        st.disconnect()
        st.quit()
