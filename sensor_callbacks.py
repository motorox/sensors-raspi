import time
from sensor_utils import calcAccel, calcGyro, calcHum, calcMagn, calcTmpTarget

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
        # enable accelerometer
        ax = (v[7]<<8)+v[6]
        ay = (v[9]<<8)+v[8]
        az = (v[11]<<8)+v[10]
        (axyz, mag) = calcAccel(ax, ay, az)
        self.data['accelx'] = axyz[0]
        self.data['accely'] = axyz[1]
        self.data['accelz'] = axyz[2]
        # enable gyroscope
        gx = (v[1]<<8)+v[0]
        gy = (v[3]<<8)+v[2]
        gz = (v[5]<<8)+v[4]
        gxyz = calcGyro(gx, gy, gz)
        self.data['gyrox'] = gxyz[0]
        self.data['gyroy'] = gxyz[1]
        self.data['gyroz'] = gxyz[2]

