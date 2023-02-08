import mcp3421 as mcp
import tca9548a as mux
from machine import I2C, Pin, SoftI2C
import time as time
from sys import stdin, stdout, exit
import select
import gc
import ujson

#Import Json file
config = ujson.load(open('diode_config.json', 'r'))




def get_adc(params):
    #print(params)
    if params[0].isdigit():
        index = int(params[0]) - 1 #1-10 give respective diode board, 0 gives index -1 which means all boards, does not exceed max length
        
        if len(sensor_dict) > index >= 0:
            result = {}
            key = config['sensors'][index]
            
            if sensor_dict[key]['mux'] != None:
                sensor_dict[key]['mux'].write_reg(index)
            result = {key: sensor_dict[key]['adc'].read_adc_v()}
            return result
        
        elif index == -1:
            result = {}
            for name in sensor_dict:
                if sensor_dict[name]['mux'] != None:
                    sensor_dict[name]['mux'].write_reg(sensor_dict[name]['mux port address'])
                
                result[name] = sensor_dict[name]['adc'].read_adc_v()
            return result
        
        else:  #  handle all other numbers
            result = 'invalid sensor number for v?'
            return result
        
    else:
        key = ''.join(params)
        if key in sensor_dict:

            if sensor_dict[key]['mux'] != None:

                sensor_dict[key]['mux'].write_reg(sensor_dict[key]['mux port address'])
                
            result = {key: sensor_dict[key]['adc'].read_adc_v()}
            return result
        else:
            result = 'invalid name of the channel for v?'
        return result  
                
            
#Funciton Builds Sensor dict
def build_sensors(config):
    sensors = {}
    for i in range(len(config['sensors'])):
        name = config['sensors'][i]
        sensors[name] = {
                'mux port address' : config['mux port address'][i],
                'slope correction 16bit': config['slope correction 16bit'][i],
                'offset correction' : config['offset correction'][i],
                'i2c port' : config['i2c'][i],
                'i2c interface' : config['i2c interface'][i]
            }
        try:#Assumes hardware i2c, if fails assumes software i2c
            sensors[name]['i2c'] = I2C(1, scl=Pin(sensors[name]['i2c port'][0]), sda=Pin(sensors[name]['i2c port'][1]))
        except:
            sensors[name]['i2c'] = SoftI2C(scl = Pin(sensors[name]['i2c port'][0]), sda = Pin(sensors[name]['i2c port'][1]))
            
        if sensors[name]['mux port address'] != None:
            sensors[name]['mux'] = mux.TCA9548A(sensors[name]['i2c'])
            sensors[name]['mux'].write_reg(sensors[name]['mux port address'])
        else:
            sensors[name]['mux'] = None
            
        sensors[name]['adc'] = mcp.MCP3421(i2c = sensors[name]['i2c'], slope = sensors[name]['slope correction 16bit'],
                              offset = sensors[name]['offset correction'])
        
        
    return sensors

sensor_dict = build_sensors(config)
    


commands = {
    'v?'.upper() : get_adc
    }


def readUSB():
    global ONCE, CONTINUOUS, last
    gc.collect()
    while stdin in select.select([stdin], [], [], 0)[0]:
        #print('Got USB serial message')
        gc.collect()
        cmd = stdin.readline()
        #print(type(cmd), repr(cmd))
        cmd = cmd.strip().upper()
        if len(cmd)>0:
            do_command(cmd)

def writeUSB(msg):
    print(ujson.dumps(msg))
    
def do_command(cmd):
    global heaters, lph
    # print('cmd', cmd)
    cmd = cmd.split()
    #print('cmd', cmd)
    if len(cmd)>1:
        params = cmd[1:]
    else:
        params = []
    cmd = cmd[0]
    if len(cmd):  # respond to command
        if cmd.upper() in commands:
            writeUSB(commands[cmd.upper()](params))       
        else:
            writeUSB('not understood')



def find_subkey(d, key_value):
    result = []
    for key, subdict in d.items():
        for sublist in subdict.items():
            if sublist == ('mux port', key_value):
                return key, sublist
    return 'key value DNE'

while True:
    readUSB()
