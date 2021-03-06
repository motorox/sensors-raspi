# sensors-raspi
Texas Instruments CC2650 sensors with Raspberry PI through Bluetooth

## stshell.py
This is a shell application to connect and read data from CC2650 sensors.
In the `sensors.ini` file, you can add a list of 2 sensors and they will be available to connect in the application. The list contains the MAC of the sensors:
```
[sensor]
sensor1_id = A0:E6:F8:AE:8C:06
sensor2_id = A0:E6:F8:B6:6B:85
```
The first one is the default one. In the example there are the MACs from my two sensors.

The shell is using `cmd` package.
List of commands:
- `h` or `?` - help, listing the commands and the description
- `list` - prints the list of configured MACs.
- `connect [id]` - connects to a sensor. The ids are 0 or 1, from the list of the sensors in the _ini_ file
- `disconnect` - disconnects from a sensor
- `read` - reads data from the connected sensor
- `quit` - quits the shell application

The data red from the sensor has the following structure:
```
{
	"accelz": 1018.84375, 
	"addr": "A0:E6:F8:B6:6B:85", 
	"accelx": 955.625, 
	"accely": 1017.53125, 
	"keys": 0, 
	"barotemp": 28.24, 
	"magnz": -50.872802734375, 
	"magnx": 17.7001953125, 
	"magny": 32.1044921875, 
	"lux": 11875, 
	"temp": 80.32170649450279, 
	"baropress": 1002.45, 
	"time": 1469707962803, 
	"gyroz": 2.69317626953125, 
	"gyrox": -0.16021728515625, 
	"gyroy": 0.92315673828125, 
	"humdtemp": 25.683835449218755, 
	"ambtemp": 27.875, 
	"humd": 46.13165283203125, 
	"celsiustemp": 26.845392496945994
}
```

## sensor.py

This file contains two classes.

`SensorTag`, the class that communicates with a sensor through Bluetooth.

`SensorCallbacks` is the one who registers callbacks to read data.

Also some functions to transform raw data from the sensors to something readable. They were inspired from TI sites.

This file can be run in the console:
```
$ python sensor.py A0:E6:F8:B6:6B:85
Reading from sensor: A0:E6:F8:B6:6B:85
(MainThread) Preparing to connect. You might need to press the side button...
[re]starting..
{"accelz": 0.0, "addr": "A0:E6:F8:B6:6B:85", "accelx": 0.0, "accely": 0.0, "keys": 0, "magnz": 0.0, "magnx": 0.0, "magny": 0.0, "gyroz": 0.0, "gyrox": 0.0, "gyroy": 0.0}
{"accelz": 1018.90625, "addr": "A0:E6:F8:B6:6B:85", "accelx": 954.3125, "accely": -1.28125, "keys": 0, "barotemp": 29.96, "magnz": -18.402099609375, "magnx": -8.941650390625, "magny": 16.693115234375, "lux": 3249, "temp": 85.89359307792137, "baropress": 1010.19, "time": 1506423349215, "gyroz": 2.6397705078125, "gyrox": 0.42724609375, "gyroy": 0.1983642578125, "humdtemp": 27.088823242187495, "ambtemp": 29.40625, "humd": 36.4957275390625, "celsiustemp": 29.940885043289647}
^C
(MainThread) joining Notification Thread
(MainThread) thread Notification Thread is alive: True
notification loop ENDED !!!
(MainThread) joining Notification Thread
(MainThread) thread Notification Thread is alive: True
notification loop ENDED !!!
```

### Steps to do on your raspberry pi (some of them) to be able to read data from the sensor
- http://mike.saunby.net/2013/04/raspberry-pi-and-ti-cc2541-sensortag.html
- https://github.com/uffebjorklund/TI-CC2650


### Links with info that was helpful
- http://processors.wiki.ti.com/index.php/CC2650_SensorTag_User's_Guide
- http://processors.wiki.ti.com/index.php/SensorTag_User_Guide
- http://www.ti.com/ww/en/wireless_connectivity/sensortag/tearDown.html
- https://github.com/energia/Energia/issues/740
- https://e2e.ti.com/blogs_/b/connecting_wirelessly/archive/2015/06/11/controlling-ultra-low-power-cc2650-wireless-mcu-from-anywhere-in-the-world
- http://pexpect.readthedocs.io/en/stable/ - spawn processes and read inputs
 
