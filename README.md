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

### Links with info that was helpful
- http://processors.wiki.ti.com/index.php/CC2650_SensorTag_User's_Guide
- http://processors.wiki.ti.com/index.php/SensorTag_User_Guide
- http://www.ti.com/ww/en/wireless_connectivity/sensortag/tearDown.html
- https://github.com/energia/Energia/issues/740

- http://pexpect.readthedocs.io/en/stable/ - spawn processes and read inputs
- 
