#!/usr/bin/env python
'''
Module that exposes a sensor tag Shell to connect to TI CC2650 sensors.
there is a "sensors.ini" config file with a list of remote Bluetooth addresses (MACs)
'''

import cmd
from ConfigParser import SafeConfigParser

from sensor import SensorCallbacks, SensorTag


class SensorTagShell(cmd.Cmd):
    '''Command line like shell for sensors'''
    intro = "Welcome to CC2650 shell. Type help or ? to list commands.\n"
    prompt = '(sensor:)> '
    st = SensorTag()
    sensors = []

    def initialize(self):
        parser = SafeConfigParser()
        parser.read(['sensors.ini'])

        try:
            self.sensors = [parser.get('sensor', 'sensor1_id'), parser.get('sensor', 'sensor2_id')]
        except:
            print 'Configuration error: Check your config files'
            raise

    def do_connect(self, args):
        """Connects to a TI CC2650 sensor TAG. You have to give an ID."""
        try:
            if len(args) == 0:
                idx = 0 # first sensor if nothing is selected
            else:
                idx = int(args) # the argument is changed to a number
            print "trying to connect sensor: %s" % self.sensors[idx]
            self.st.connect(self.sensors[idx], SensorCallbacks)
        except Exception, e:
            print str(e)
    def do_disconnect(self, args):
        """Disconnects from a sensor."""
        self.st.disconnect()
    def do_read(self, args):
        """Reads data from the connected sensor. If you there is one."""
        print "Sensor data:\n %s" % self.st.get_data()
    def do_quit(self, args):
        """Quits the program """
        print "Quitting ..."
        self.st.quit()
        # raise SystemExit
        return True
    def do_list(self, args):
        """lists the sensors that are available for reading. Indexes are 0 based"""
        print self.sensors

if __name__ == "__main__":
    sts = SensorTagShell()
    sts.initialize()
    sts.cmdloop()
