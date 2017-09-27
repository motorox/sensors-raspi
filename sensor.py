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

import sys
import json
import logging
import threading
import time
import pexpect
import sensor_callbacks

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s',)

class Sensor(object):
    '''Sensor class provides connects to a sensor, reads and writes data'''
    notificationLoop = False
    callbacks = None
    def __init__(self):
        # if bluetooth_adr <> "":
        #     self.con = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
        # else:
        self.cb = {}
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: sensor.py <sensor MAC>"
        sys.exit(1)
    else:
        print 'Reading from sensor: ' + sys.argv[1]
        st = Sensor()
        st.connect(sys.argv[1], sensor_callbacks.SensorCallbacks)
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
