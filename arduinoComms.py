import serial
import time
import sys
import glob

# global variables for module
startMarker = "<"
endMarker = ">"



#========================

def valToArduino(pulse_on, pulse_delta,number_of_stimuli,predelay,everything_armed):
    sendStr = "%s,%s,%s,%s,%s" %(pulse_on,pulse_delta,number_of_stimuli,predelay,everything_armed)
    #print("SENDSTR %s" %(sendStr))
    sendToArduino(sendStr)

#========================
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
'''
def listSerialPorts():
    #from https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
    import serial.tools.list_ports
    comlist = serial.tools.list_ports.comports()
    connected = []

    for element in comlist:
        try:
            s = serial.Serial(element.device)
            s.close()
            connected.append(element.device)
        except (OSError, serial.SerialException):
            pass
    return connected
'''
#========================

def setupSerial(serPort):

    global ser
    global serial_connection
    baudRate = 9600
    try:
        ser = serial.Serial(serPort, baudRate)
        print("Serial port " + serPort + " opened  Baudrate " + str(baudRate))
        serial_connection = True
        waitForArduino()
    except (OSError, serial.SerialException):
        print("Could not connect to selected port!")
        serial_connection = False
        pass


#========================

def closeSerial():

    global ser
    if 'ser' in globals():
        ser.close()
        print("Serial Port Closed")
    else:
        print("Serial Port Not Opened")

#========================

def sendToArduino(sendStr):

    global startMarker, endMarker, ser

    ser.write(str.encode(startMarker))
    ser.write(str.encode(sendStr))
    ser.write(str.encode(endMarker))



#===========================

def recvFromArduino(): # timeout in seconds eg 1.5

    global startMarker, endMarker, ser
    dataBuf = ""
    x = "z"

    ser.flushInput()
    while x != endMarker:
        a = ser.read()
        x = a.decode()
        if x != startMarker and x !=endMarker:
            dataBuf = dataBuf + x
        if x == endMarker:
            pass
    return dataBuf

#============================



def waitForArduino():

   # wait until the Arduino sends 'Arduino Ready' - allows time for Arduino reset
   # it also ensures that any bytes left over from a previous message are discarded

    print("Waiting to hear from Arduino")
    msg = ""
    while msg.find("Arduino is ready") == -1:
        arduino_ready = False
        msg = recvFromArduino()
        print(msg)

    else:
        print("Arduino connected!")
        arduino_ready = True
    return arduino_ready
