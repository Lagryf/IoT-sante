import machine
import ssd1306
import time 
import pyb
from pyb import ADC
import random

machine.Pin(machine.Pin.cpu.C2, mode=machine.Pin.IN)
machine.Pin('A0', machine.Pin.OUT).low()
machine.Pin('C3', machine.Pin.OUT).high()

i2c = machine.SoftI2C(scl=machine.Pin('A15'), sda=machine.Pin('C10'))
# Power Display
machine.Pin('C13', machine.Pin.OUT).low()
machine.Pin('A8', machine.Pin.OUT).high()

oled = ssd1306.SSD1306_I2C(128,32,i2c)
rtc = machine.RTC()
rtc.datetime((2020, 1, 21, 2, 1, 2, 36, 0))

# Global variable
menu = "watch"
value_hearth = 0
value_n = 0
value_menu = 10
maximum = 1
minimum = 1000

def time_now():
    oled.fill(0)
    rtcdate = rtc.datetime()
    if rtcdate[4] <= 9 :
        oled.text('0' + str(rtcdate[4]), 45, 13)
    else:
        oled.text(str(rtcdate[4]), 45, 13)
    if rtcdate[5] <= 9 :
        oled.text('0' + str(rtcdate[5]), 65, 13)
    else:
        oled.text(str(rtcdate[5]), 65, 13)
        
    if rtcdate[6] % 2 == 0 :
    	oled.text(':', 60, 13)
    oled.show()
    
def normalize_value(prev_value_n, prev_value, value):
    return prev_value_n + (prev_value - value)
    
    
def menu_selection(menu):
    if menu == "watch":
        return "hearth"
    if menu == "hearth":
        return "pot_game"
    if menu == "pot_game":
        return "chrono"
    return "watch"
    
def hearth_now(prev_value_n, value_hearth, width):
	if width == 128:
	    oled.fill(0)
	    width = 0
	prev_value = value_hearth
	value_hearth = ADC("C2").read()
	value_n = normalize_value(prev_value_n, prev_value, value_hearth)
	if value_n < 0 or value_n/7 > 64:
	    value_n = 0
	oled.text('.', width, int(value_n/7))
	oled.show()
	return value_n, value_hearth

def get_bpm(prev_value_n, value_n, beats):
    if prev_value_n - value_n > 20:
        return beats + 1
    return beats

def pot_game_init():
    oled.fill(0)
    oled.text("find the right",5,0)
    oled.text("combination", 10, 10)
    oled.show()
    rng = []
    for i in range(3) : 
        rng.append(random.randint(0,99))
    return rng

def pot_game(rng, success):
    
    position = ADC("A5").read()
    if rng[success] == position :
        return success + 1
    return success  
def pot_game_success(rng, success):
    if success != 0 :
        pyb.LED(success).on()
        oled.text(str(rng[success - 1]), 10 + success * 20, 20)
        oled.show()
    if success == 3:
        oled.fill(0)
        for i in range(3):
            oled.text("Success !", 5, 0)
            oled.text(str(rng[i]), 10 + i * 20, 20)
            oled.show()
            pyb.LED(1).off()            
            pyb.LED(2).off()
            pyb.LED(3).off()
            time.sleep(0.4)
            pyb.LED(1).on()            
            pyb.LED(2).on()
            pyb.LED(3).on()
            time.sleep(0.4)
        pyb.LED(1).off()            
        pyb.LED(2).off()
        pyb.LED(3).off()
        return 0, False  
    return success, True

def chrono(value_button):
    prev_value = value_button
    if prev_value == 0 and value_button == 0 :
        deci = 0
        second = 0
        minute = 0
        while True:
            prev_value = value_button
            value_button = ADC("A6").read()
            if prev_value == 0 and value_button == 0 :
                break
            oled.fill(0)
            deci += 1
            if deci == 10 :
                deci = 0
                second += 1
            if second == 60 :
                second = 0
                minute += 1
            oled.fill(0)
            if minute <= 9 :
                oled.text('0' + str(minute), 45, 13)
            else:
                oled.text(str(minute), 45, 13)
            if second <= 9 :
                oled.text('0' + str(second), 65, 13)
            else:
                oled.text(str(second), 65, 13)
            oled.text('.', 80, 13)
            oled.text(':', 60, 13)
            oled.text(str(deci), 85, 13)
            oled.show()
            time.sleep(0.1)
        
        #waiting loop
        time.sleep(0.5)
        while True:
            value_button = ADC("A6").read()
            if value_button == 0:
                time.sleep(0.2)
                value_button = ADC("C0").read()
                if value_button == 0:
                    break
            else:
                chrono(value_button)
                break
width = 0
success = 0
init = False
pyb.LED(2).off()
beats = 0
minuteur = False
while True:
    if menu == "chrono":
        init = False
        chrono(value_menu) 
        menu = menu_selection(menu)  
    prev_value = value_menu
    value_menu = ADC("A6").read()
    if prev_value == 0 and value_menu == 0 :
        menu = menu_selection(menu)
        time.sleep(0.2)
        if menu == "hearth" :
            oled = ssd1306.SSD1306_I2C(128,64,i2c)
            beats = 0
        else:
            oled = ssd1306.SSD1306_I2C(128,32,i2c)
    if menu == "watch" :
        width = 0
        time_now()
    elif menu == "hearth":
        if not minuteur : 
            start_time = time.time()
            minuteur = True
        prev_value_n = value_n
        width += 1
        #hearth_beat_test()
    	value_n, value_hearth = hearth_now(prev_value_n, value_hearth, width)
    	if width == 128:
    	    width = 0
    	if width == 0:
    	    oled.text(str(beats * 4) + " BPM", 30, 50)
    	    beats = 0
    	    oled.show()
    	    minuteur = False  
    	beats = get_bpm(prev_value_n, value_n, beats)
    if menu == "pot_game" :
        if not init :
            rng = pot_game_init()
            init = True
        success = pot_game(rng, success)
        success, init = pot_game_success(rng, success)
    
    
    
    
    
    
    
    
    
    
    
