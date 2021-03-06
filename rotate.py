#!/usr/bin/env python2.7

#######
# Note: This is intended for the Kaby Lake HP Spectre x360. It was tested on model 13t-w000,
#       but should work on any tablet with the same touchscreen (name: ''ELAN0732:00 04F3:2493')
#       If it doesn't work, check the output of 'xinput --list', and replace the touchscreen id,
#       trackpad name, and pen (if applicable) at the top of the script with your values.


from time import sleep
from os import path as op
import sys
from subprocess import check_call, check_output
from glob import glob


# Your device names go here if different.
TOUCHSCREEN = 'ELAN0732:00 04F3:2493'
TOUCHPAD    = 'SynPS/2 Synaptics TouchPad'
PEN         = 'ELAN0732:00 04F3:22E1 Pen Pen (0)'

disable_touchpads = True


def bdopen(fname):
    return open(op.join(basedir, fname))


def read(fname):
    return bdopen(fname).read()


for basedir in glob('/sys/bus/iio/devices/iio:device*'):
    if 'accel' in read('name'):
        break
else:
    sys.stderr.write("Can't find an accellerator device!\n")
    sys.exit(1)


scale = float(read('in_accel_scale'))

g = 7.0  # (m^2 / s) sensibility, gravity trigger

STATES = [
    {'rot': 'normal', 'coord': '1 0 0 0 1 0 0 0 1', 'touchpad': 'enable',
     'check': lambda x, y: y <= -g},
    {'rot': 'inverted', 'coord': '-1 0 1 0 -1 1 0 0 1', 'touchpad': 'disable',
     'check': lambda x, y: y >= g},
    {'rot': 'left', 'coord': '0 -1 1 1 0 0 0 0 1', 'touchpad': 'disable',
     'check': lambda x, y: x >= g},
    {'rot': 'right', 'coord': '0 1 0 -1 0 1 0 0 1', 'touchpad': 'disable',
     'check': lambda x, y: x <= -g},
]


def rotate(state):
    s = STATES[state]
    check_call(['xrandr', '-o', s['rot']])

    check_call(['xinput', 'set-prop', TOUCHSCREEN, 'Coordinate Transformation Matrix',] + s['coord'].split())
    
    if "Pen (0)" in check_output(['xinput', '--list']).decode("utf-8"):
        check_call(['xinput', 'set-prop', PEN, 'Coordinate Transformation Matrix',] + s['coord'].split())

    if disable_touchpads:
        check_call(['xinput', s['touchpad'], TOUCHPAD])


def read_accel(fp):
    fp.seek(0)
    return float(fp.read()) * scale


if __name__ == '__main__':

    accel_x = bdopen('in_accel_x_raw')
    accel_y = bdopen('in_accel_y_raw')

    current_state = None

    while True:
        x = read_accel(accel_x)
        y = read_accel(accel_y)
        for i in range(4):
            if i == current_state:
                continue
            if STATES[i]['check'](x, y):
                current_state = i
                rotate(i)
                break
        sleep(1)
