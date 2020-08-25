import PySimpleGUI as sg
import numpy as np
import sys
import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import arduinoComms as aC
#import arduinoCheckForData as cD


def define_squarewave(pulse_on, pulse_off,train_length,number_of_stimuli, longtrain=None):

    #pulse_duration = pulse_on + pulse_off
    if longtrain is True:
        train_length = train_length * 1000
        pulse_maximum = (train_length) / number_of_stimuli
        train_length = train_length / 1000
    else:
        pulse_maximum = (train_length) / number_of_stimuli

    if number_of_stimuli == 1:
        pulse_maximum = pulse_on
        pulse_delta = pulse_on

    #pulse_delta = pulse_maximum - pulse_duration
    else:
        pulse_delta = pulse_maximum - pulse_on

    parameters = {"train_length": train_length,
                  "number_of_stimuli": int(number_of_stimuli),
                 # "pulse_duration": int(pulse_duration),
                  "pulse_maximum": int(pulse_maximum),
                  "pulse_delta": int(pulse_delta)
                 }
    return parameters

def plot_wave(parameter_dict, pulse_on, pulse_off, predelay):
    pulse_on_array = np.full(int(pulse_on,), int(5))
    #pulse_off_array = np.zeros((int(pulse_off+parameter_dict["pulse_delta"])),dtype=int)
    pulse_off_array = np.zeros((int(parameter_dict["pulse_delta"])),dtype=int)
    #plot_pulse = np.concatenate([pulse_start,pulse_on_array,pulse_off_array])
    if predelay > 0:
        predelay_array = np.zeros(int(predelay))
        pulse_on_off = np.concatenate([pulse_on_array,pulse_off_array])
        y_data = np.tile(pulse_on_off,parameter_dict["number_of_stimuli"])
        y_data = np.concatenate([predelay_array, y_data])
    else:
        pulse_on_off = np.concatenate([pulse_on_array,pulse_off_array])
        y_data = np.tile(pulse_on_off,parameter_dict["number_of_stimuli"])
    return y_data

def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


range_1 = np.arange(200,5001).tolist()
range_2 = np.arange(1,101).tolist()
range_3 = np.arange(1,101).tolist()
range_long = np.arange(0.5,301,0.5).tolist()
global connected_port
connected_port = ""

sg.theme('Black')   # Add a touch of color
# All the stuff inside your window. 17, 14, 17
layout = [
          [sg.Checkbox('Predelay [ms]', default=False, key="_PREDELAYCHECK_",enable_events=True, disabled=False), sg.Slider(range=(0,2000), resolution=5, disabled=True, default_value=0, size=(50,15), orientation='horizontal',enable_events=True, key="_PREDELAY_", font=('Helvetica', 12))],
          [sg.Text('Pulse on [ms]', pad=((10,2),(0,0))), sg.Slider(range=(1,50), default_value=1, size=(50,15), orientation='horizontal',enable_events=True, key="_PULSEON_", font=('Helvetica', 12))],
          [sg.Text('Pulse off [ms]', pad=((10,2),(0,0)), visible=False), sg.Slider(range=(1,20),visible=False,default_value=1, size=(50,15), orientation='horizontal',enable_events=True, key="_PULSEOFF_", font=('Helvetica', 12))],

          [sg.Checkbox('Train length', default=False, key="_TRAINLENGTHCHECK_",enable_events=True),sg.Text('[ms]', key="_TRAINUNIT_", justification="left", pad=(0,0)),
           sg.Slider(range=(200,5000), resolution=0.5, default_value=1000, disable_number_display=False,size=(50,15), orientation='horizontal',enable_events=True, key="_TRAINLENGTH_", font=('Helvetica', 12))],

          [sg.Checkbox('Frequency [Hz]',pad=(7,2), default=False, key="_FREQUENCYCHECK_",enable_events=True),
           sg.Slider(range=(1,100), resolution=.2, default_value=30, disable_number_display=False, size=(50,15), orientation='horizontal',enable_events=True, key="_FREQUENCY_", font=('Helvetica', 12))],

          [sg.Checkbox('Number of stimuli', default=False, key="_NOFSTIMULICHECK_",enable_events=True),
           sg.Slider(range=(1,100), resolution=1, default_value=50, disable_number_display=False, size=(50,15), orientation='horizontal',enable_events=True, key="_NUMBEROFSTIMULI_", font=('Helvetica', 12))],

          [sg.Canvas(size=(50, 20), key='_PLOT_')],
          [sg.Checkbox('Train length >5 s', default=False, key="_LONGTRAIN_",enable_events=True, disabled=True),
          sg.Checkbox('Pulse on >50 ms', default=False, key="_LONGPULSE_", enable_events=True, disabled=True),
          sg.Checkbox('Fixate X-Axis', default=False, key="_FIXAXIS_",enable_events=True, disabled=True),
          sg.Spin([i for i in range(200,5000,50)], initial_value=1000, visible=False, key="_FIXVALUE_",enable_events=True)],

          [sg.Output(size=(100, 7), key="_output_")],
          [sg.Button('Send to Arduino', key="_SEND_", enable_events=True, disabled=True), sg.Button(button_text=connected_port, key="_DISPLAYPORT_",disabled=True)]
        ]

port_list = aC.serial_ports()

layout_port = [
            [sg.Text('Available serial ports:')],
            [sg.Combo(values=(port_list), key="_PORTLIST_",enable_events=True, size=(30, 3))],
            [sg.Button('Connect to port', key="_PORTSEND_", enable_events=True),sg.Button('Proceed to GUI', key="_PORTPROCEED_", enable_events=True, disabled=False),sg.Button('Close application', key="_PORTCLOSEAPP_", enable_events=True)],
            [sg.Output(size=(100, 7), key="_PORT_OUTPUT_")]
]

global status
global allow_to_send
global serial_connection
global port_selected
port_selected = False
serial_connection = False

status = []
allow_to_send = False
window_2_active = False
# Create the Window


plt.style.use('dark_background')
fig = Figure(figsize=[7,4])
ax = fig.add_subplot(111)
ax.grid()
ax.set_xlabel("Time [ms]")
ax.set_ylabel("Voltage [V]")
ax.set_xlim(left=None, right=None, auto=True)
ax.set_ylim(0,5.2)

#aC.setupSerial('COM3')
window_port = sg.Window("TTL Trigger - select Port", layout_port, finalize=True)

while True:
    if port_selected == False and window_2_active == False:

        event_port,values_port = window_port.read()
        window_port["_PORTPROCEED_"].update(disabled=True)

        if event_port == "_PORTSEND_":
            try:
                portstatus = aC.setupSerial(values_port["_PORTLIST_"])
                connected_port = values_port["_PORTLIST_"]
                window_port["_PORTPROCEED_"].update(disabled=False)
            except:
                pass

        if event_port == "_PORTPROCEED_" and window_2_active == False:
                port_selected = portstatus #set to portstatus when ready to compile, set to TRUE when working on GUI to bypass port selection
                window_2_active = True
                window_port.close()
                window = sg.Window('TTL Trigger', layout, finalize=True)
                canvas_elem = window['_PLOT_']
                canvas = canvas_elem.TKCanvas
                fig_agg = draw_figure(canvas, fig)

        if event_port == "_PORTCLOSEAPP_" or event_port is None:
            print("Closing Application")
            break


    if window_2_active==True:
        #window = sg.Window('TTL Trigger', layout, finalize=True)


        allow_to_send = False

        #read all current events and values
        event,values = window.read(timeout = 100)
        window["_DISPLAYPORT_"].update(text=connected_port)
        #save the boolean values of the checkboxes in the status list
        status=[values["_TRAINLENGTHCHECK_"], values["_FREQUENCYCHECK_"], values["_NOFSTIMULICHECK_"]]
        #count all true == checked states of the checkboxes
        trues = status.count(True)
        long =  values["_LONGTRAIN_"]
        window["_TRAINUNIT_"].update(text_color='white')

        #if event in ('\r', 'special 16777220', 'special 16777221'):


        #if no checkbox is checked, freeze all sliders, makes sure the checkboxes are
        #available and clear output box
        if trues == 0:
            window["_SEND_"].update(disabled=True)
            window["_FIXAXIS_"].update(disabled=True)
            window["_FIXVALUE_"].update(visible=False)
            window["_LONGTRAIN_"].update(disabled=True)
            window["_LONGPULSE_"].update(disabled=True)
            if long == 0:
                window["_TRAINUNIT_"].update("[ms]")
            if long == 1:
                window["_TRAINUNIT_"].update("[s]")

            if values["_LONGPULSE_"] == 0:
                window["_PULSEON_"].update(range=(1,50))

            window.FindElement('_TRAINLENGTH_').Update(disabled=True)
            window.FindElement('_FREQUENCY_').Update(disabled=True)
            window.FindElement('_NUMBEROFSTIMULI_').Update(disabled=True)

            window.FindElement('_TRAINLENGTHCHECK_').Update(disabled=False)
            window.FindElement('_FREQUENCYCHECK_').Update(disabled=False)
            window.FindElement('_NOFSTIMULICHECK_').Update(disabled=False)
            ax.cla()                    # clear the subplot
            ax.grid()
            if long == 0:
                ax.set_xlabel("Time [ms]")
            elif long == 1:
                ax.set_xlabel("Time [s]")
            ax.set_ylabel("Voltage [V]")
            ax.set_ylim(0,5.2)
            fig_agg.draw()
            window.FindElement('_output_').Update('')

        #if one checkbox was checked, unfreeze sliders, make again sure all boxes can be checked
        #and clear output box
        if trues == 1:
            window["_SEND_"].update(disabled=True)
            window["_FIXAXIS_"].update(disabled=True)
            window["_FIXVALUE_"].update(visible=False)
            window["_LONGTRAIN_"].update(disabled=True)
            window["_LONGPULSE_"].update(disabled=True)
            if long == 0:
                window["_TRAINUNIT_"].update("[ms]")
            if long == 1:
                window["_TRAINUNIT_"].update("[s]")

            if values["_LONGPULSE_"] == 0:
                window["_PULSEON_"].update(range=(1,50))

            window.FindElement('_TRAINLENGTHCHECK_').Update(disabled=False)
            window.FindElement('_FREQUENCYCHECK_').Update(disabled=False)
            window.FindElement('_NOFSTIMULICHECK_').Update(disabled=False)

            window.FindElement('_TRAINLENGTH_').Update(disabled=False)
            window.FindElement('_FREQUENCY_').Update(disabled=False)
            window.FindElement('_NUMBEROFSTIMULI_').Update(disabled=False)

            ax.cla()                    # clear the subplot
            ax.grid()
            if long == 0:
                ax.set_xlabel("Time [ms]")
            elif long == 1:
                ax.set_xlabel("Time [s]")
            ax.set_ylabel("Voltage [V]")
            ax.set_ylim(0,5.2)
            fig_agg.draw()
            window.FindElement('_output_').Update('')
        #eventually, if two boxes where checked, disable the one left, calculate its value,
        #set the corresponding slider to that value and pass all the values to the pulse function
        #do this for every possible combination - find better way to do it?!
        if trues == 2:
            window["_SEND_"].update(disabled=False)
            window["_FIXAXIS_"].update(disabled=False)
            window["_LONGTRAIN_"].update(disabled=False)
            window["_LONGPULSE_"].update(disabled=False)

            if values["_LONGPULSE_"] == 1:
                window["_PULSEON_"].update(range=(1,5000))

            if values["_LONGPULSE_"] == 0:
                window["_PULSEON_"].update(range=(1,50))

            if long == 0:
                window["_TRAINLENGTH_"].update(range=(200,5000))
                window["_NUMBEROFSTIMULI_"].update(range=(1,100))
                window["_TRAINUNIT_"].update("[ms]")

                if values["_TRAINLENGTHCHECK_"] and values["_FREQUENCYCHECK_"] == True:
                    window.FindElement('_NOFSTIMULICHECK_').Update(disabled=True)
                    window.FindElement('_NUMBEROFSTIMULI_').Update(disabled=True)
                    number_of_stimuli = (values["_TRAINLENGTH_"]/1000) * values["_FREQUENCY_"]
                    window['_NUMBEROFSTIMULI_'].update(number_of_stimuli)
                    frequency = values["_FREQUENCY_"]
                    mysquarewave = define_squarewave(values["_PULSEON_"], values["_PULSEOFF_"],train_length=values["_TRAINLENGTH_"], number_of_stimuli=number_of_stimuli)

                if values["_TRAINLENGTHCHECK_"] and values["_NOFSTIMULICHECK_"] == True:
                    window.FindElement('_FREQUENCYCHECK_').Update(disabled=True)
                    window.FindElement('_FREQUENCY_').Update(disabled=True)
                    frequency = values["_NUMBEROFSTIMULI_"] / (values["_TRAINLENGTH_"]/1000)
                    window['_FREQUENCY_'].update(frequency)
                    mysquarewave = define_squarewave(values["_PULSEON_"], values["_PULSEOFF_"],train_length=values["_TRAINLENGTH_"], number_of_stimuli=values["_NUMBEROFSTIMULI_"])

                if values["_NOFSTIMULICHECK_"] and values["_FREQUENCYCHECK_"] == True:

                    window.FindElement('_TRAINLENGTHCHECK_').Update(disabled=True)
                    window.FindElement('_TRAINLENGTH_').Update(disabled=True)
                    window["_TRAINUNIT_"].update(text_color='grey')

                    train_length = (values["_NUMBEROFSTIMULI_"] / values["_FREQUENCY_"]) * 1000
                    window['_TRAINLENGTH_'].update(train_length)
                    frequency = values["_FREQUENCY_"]
                    mysquarewave = define_squarewave(values["_PULSEON_"], values["_PULSEOFF_"],train_length=train_length, number_of_stimuli=values["_NUMBEROFSTIMULI_"])


            elif long == 1:
                    window["_TRAINLENGTH_"].update(range=(0.5,300))
                    window["_NUMBEROFSTIMULI_"].update(range=(1,1000))
                    window["_TRAINUNIT_"].update("[s]")

                    if values["_TRAINLENGTHCHECK_"] and values["_FREQUENCYCHECK_"] == True:
                        window.FindElement('_NOFSTIMULICHECK_').Update(disabled=True)
                        window.FindElement('_NUMBEROFSTIMULI_').Update(disabled=True)
                        number_of_stimuli = (values["_TRAINLENGTH_"]) * values["_FREQUENCY_"]
                        window['_NUMBEROFSTIMULI_'].update(number_of_stimuli)
                        frequency = values["_FREQUENCY_"]
                        mysquarewave = define_squarewave(values["_PULSEON_"], values["_PULSEOFF_"],train_length=values["_TRAINLENGTH_"], number_of_stimuli=number_of_stimuli, longtrain = True)

                    if values["_TRAINLENGTHCHECK_"] and values["_NOFSTIMULICHECK_"] == True:
                        window.FindElement('_FREQUENCYCHECK_').Update(disabled=True)
                        window.FindElement('_FREQUENCY_').Update(disabled=True)
                        frequency = values["_NUMBEROFSTIMULI_"] / (values["_TRAINLENGTH_"])
                        window['_FREQUENCY_'].update(frequency)
                        mysquarewave = define_squarewave(values["_PULSEON_"], values["_PULSEOFF_"],train_length=values["_TRAINLENGTH_"], number_of_stimuli=values["_NUMBEROFSTIMULI_"], longtrain = True)

                    if values["_NOFSTIMULICHECK_"] and values["_FREQUENCYCHECK_"] == True:
                        window.FindElement('_TRAINLENGTHCHECK_').Update(disabled=True)
                        window.FindElement('_TRAINLENGTH_').Update(disabled=True)
                        window["_TRAINUNIT_"].update(text_color='grey')

                        train_length = (values["_NUMBEROFSTIMULI_"] / values["_FREQUENCY_"])
                        window['_TRAINLENGTH_'].update(train_length)
                        frequency = values["_FREQUENCY_"]
                        mysquarewave = define_squarewave(values["_PULSEON_"], values["_PULSEOFF_"],train_length=train_length, number_of_stimuli=values["_NUMBEROFSTIMULI_"], longtrain = True)
            #clear outputbox before it gets updated with new data outputbox
            window.FindElement('_output_').Update('')

            #check if pulse delta value is negative (meaning overlapping pulses)
            #and print error message

            if mysquarewave["pulse_delta"] <= 0:

                ax.cla()                    # clear the subplot
                if long == 0:
                    ax.set_xlabel("Time [ms]")
                elif long == 1:
                    ax.set_xlabel("Time [s]")
                ax.set_ylabel("Voltage [V]")
                ax.set_ylim(0,5.2)
                ax.set_xlim(left=None, right=None, auto=True)
                ax.grid()
                fig_agg.draw()
                print("This configuration is not possible!")

            #if everything is ok print the calculated values to the outputbox
            else:
                allow_to_send = True
                if values["_PREDELAYCHECK_"] == True:
                    window["_PREDELAY_"].update(disabled=False)
                    predelay = values["_PREDELAY_"]
                else:
                    window["_PREDELAY_"].update(disabled=True)
                    predelay = 0

                print("Predelay [ms]:", int(predelay))
                if long == 0:
                    print("Train length [ms]:", round(mysquarewave["train_length"],3))
                elif long == 1:
                    print("Train length [s]:", round(mysquarewave["train_length"],3))

                print("Frequency [Hz]:", round(frequency, 2))
                print("Number of stimuli:", mysquarewave["number_of_stimuli"])
                #print("Duration of pulse [ms]:", mysquarewave["pulse_duration"])
                print("Maximum pulse duration possible [ms]:", mysquarewave["pulse_maximum"])
                print("Time inbetween pulses [ms]:", mysquarewave["pulse_delta"])
                my_ydata = plot_wave(mysquarewave,values["_PULSEON_"], values["_PULSEOFF_"], predelay)

                ax.cla()
                if values["_FIXAXIS_"] == True:
                    window.Refresh()
                    window["_FIXVALUE_"].update(visible=True)
                    ax.set_xlim(0,int(values["_FIXVALUE_"]))
                    ax.set_xlabel("Time [ms]")
                    ax.set_ylabel("Voltage [V]")
                    ax.set_ylim(0,5.2)
                    ax.plot(my_ydata, color='red', linewidth=1.5)
                    ax.grid()
                    fig_agg.draw()

                else:
                    window["_FIXVALUE_"].update(visible=False)

                    ax.set_xlabel("Time [ms]")
                    ax.set_ylabel("Voltage [V]")
                    ax.set_ylim(0,5.2)
                    ax.set_xlim(left=None, right=None, auto=True)
                    if long == 1:
                        ax.set_xlabel("Time [s]")
                        #https://stackoverflow.com/questions/10171618/changing-plot-scale-by-a-factor-in-matplotlib
                        ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/1000))
                        ax.xaxis.set_major_formatter(ticks_x)
                    ax.grid()

                    if values["_NUMBEROFSTIMULI_"] >= 150:
                        my_linewidth = 0.25
                    else:
                        my_linewidth = 1.5
                    ax.plot(my_ydata, color='red', linewidth=my_linewidth)
                    fig_agg.draw()

                if event == "_SEND_"and allow_to_send == True:
                    aC.valToArduino(values["_PULSEON_"], mysquarewave["pulse_delta"],mysquarewave["number_of_stimuli"],predelay,1)
        #if window was closed, break the programm
        if event is None:
            window_2_active = False
            break

window_port.close()
window.close()
