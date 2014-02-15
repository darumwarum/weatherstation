#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import time as timer
import logging as log
log.basicConfig(level=log.INFO)

from time import *

from tinkerforge.ip_connection import IPConnection
from tinkerforge.ip_connection import Error
from tinkerforge.bricklet_lcd_20x4 import LCD20x4
from tinkerforge.bricklet_ambient_light import AmbientLight
from tinkerforge.bricklet_humidity import Humidity
from tinkerforge.bricklet_barometer import Barometer

class WeatherStation:
    HOST = "localhost"
    PORT = 4223

    ipcon = None
    lcd = None
    lcd_clear = False
    al = None
    hum = None
    baro = None

    def __init__(self):
        self.ipcon = IPConnection()
        while True:
            try:
                self.ipcon.connect(WeatherStation.HOST, WeatherStation.PORT)
                break
            except Error as e:
                log.error('Connection Error: ' + str(e.description))
                timer.sleep(1)
            except socket.error as e:
                log.error('Socket error: ' + str(e))
                timer.sleep(1)

        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE,
                                     self.cb_enumerate)
        self.ipcon.register_callback(IPConnection.CALLBACK_CONNECTED,
                                     self.cb_connected)

        while True:
            try:
                self.ipcon.enumerate()
                break
            except Error as e:
                log.error('Enumerate Error: ' + str(e.description))
                timer.sleep(1)  

    def start(self):
        t = 10
        extended_timer = 10      
        try:
            while True:
                if self.lcd:
                    self.write_date(0, 0)
                    self.write_time(1, 0)
                    t = t + 1
                    if t >= extended_timer:
                        if self.baro:
                            self.write_temperatur(2, 0)
                        if self.hum:
                            self.write_humidity(3, 0)
                        t = 0
                timer.sleep(1)
        except KeyboardInterrupt:    
            if weather_station.ipcon != None:
                weather_station.ipcon.disconnect()
            return

    def init_lcd(self, uid):
        try:
            self.lcd = LCD20x4(uid, self.ipcon)
            self.lcd.clear_display()
            self.lcd.backlight_on()
            log.info('LCD 20x4 initialized')
        except Error as e:
            log.error('LCD 20x4 init failed: ' + str(e.description))
            self.lcd = None
            
    def init_ambientlight(self, uid):
        try:
            self.al = AmbientLight(uid, self.ipcon)
            self.al.set_illuminance_callback_period(1000)
            self.al.register_callback(self.al.CALLBACK_ILLUMINANCE,
                                              self.cb_illuminance)
        except Error as e:
            log.error('Ambient Light init failed: ' + str(e.description))
            self.al = None
    
      
    def init_barometer(self, uid):
        try:
            self.baro = Barometer(uid, self.ipcon)
        except Error as e:
            log.error('Barometer init failed: ' + str(e.description))
            self.baro = None
    
    def init_humidity(self, uid):
        try:
            self.hum = Humidity(uid, self.ipcon)
        except Error as e:
            log.error('Humidity init failed: ' + str(e.description))
            self.hum = None
    
    def write_time(self, line, start_position):
        lt = localtime()
        hour, minute, second = lt[3:6]
        self.lcd.write_line(line, start_position, "Time:       %02i:%02i:%02i" % (hour, minute, second))

    def write_date(self, line, start_position):
        lt = localtime()
        year, month, day = lt[0:3]
        self.lcd.write_line(line, start_position, "Date:     %02i.%02i.%04i" % (day, month, year))

    def write_temperatur(self, line, start_position):
        try:
            temperature = self.baro.get_chip_temperature()
            text = 'Temp:       %5.2f \xDFC' % (temperature / 100.0)
            self.lcd.write_line(line, start_position, text)
        except Error as e:
            log.error('Could not get temperature: ' + str(e.description))
            return        
    
    def write_humidity(self, line, start_position):
        try:
            h = self.hum.get_humidity()
            text = 'Humidity:   %6.2f %%' % (h / 10.0)
            self.lcd.write_line(line, start_position, text)
        except Error as e:
            log.error('Could not get temperature: ' + str(e.description))
            return 

    def cb_illuminance(self, illuminance):
        if self.lcd is not None:
            i = illuminance / 10.0 
            if i < 0.5 and self.lcd.is_backlight_on():
                self.lcd.backlight_off()
            elif i >= 0.5 and not self.lcd.is_backlight_on():
                self.lcd.backlight_on()

    def cb_enumerate(self, uid, connected_uid, position, hardware_version,
                     firmware_version, device_identifier, enumeration_type):
        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == LCD20x4.DEVICE_IDENTIFIER:
                self.init_lcd(uid)
            elif device_identifier == AmbientLight.DEVICE_IDENTIFIER:
                self.init_ambientlight(uid)
            elif device_identifier == Humidity.DEVICE_IDENTIFIER:
                self.init_humidity(uid)
            elif device_identifier == Barometer.DEVICE_IDENTIFIER:  
                self.init_barometer(uid)
         

    def cb_connected(self, connected_reason):
        if connected_reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            log.info('Auto Reconnect')
            while True:
                try:
                    self.ipcon.enumerate()
                    break
                except Error as e:
                    log.error('Enumerate Error: ' + str(e.description))
                    timer.sleep(1)

if __name__ == "__main__":
    log.info('Weather Station: Start')

    weather_station = WeatherStation()
    weather_station.start()


    log.info('Weather Station: End')
