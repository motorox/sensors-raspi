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

tosigned = lambda n: float(n-0x10000) if n > 0x7fff else float(n)
tosignedbyte = lambda n: float(n-0x100) if n > 0x7f else float(n)

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
    return t

def calcTmpTarget(objT, ambT):
    Vobj2 = tosigned(objT) * 0.00000015625
    Tdie2 = tosigned(ambT)/128.0 + 273.15
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
