#!/usr/bin/env python

import sys, os, time
import xml.dom.minidom

import PyTango
import taurus
from taurus.external.qt import QtCore, QtGui, uic
import fandango

import rcc_pinger

SEPARATOR = "#"
DELAY_INTEGER_DIGITS = 11
DELAY_DECIMAL_DIGITS = 0

# Current and Voltage Ranges #
MAX_CURRENT_VALUE = 60e-3
MIN_CURRENT_VALUE = 0
MAX_VOLTAGE_VALUE = 12.5e3
MIN_VOLTAGE_VALUE = 0

 # Vertical Pinger Magent
PMV_01_DEVICE = "SR/DI/PMV-01"
PMV_01_DOOR_INTERLOCK = ""
PMV_01_PS_INTERLOCK = ""
PMV_01_PS_HV = ""

# Horizontal Pinger Magent
PMH_01_DEVICE = "SR/DI/PMH-01"
PMH_01_DOOR_INTERLOCK = ""
PMH_01_PS_INTERLOCK = ""
PMH_01_PS_HV = ""

# PLC device
PM_PLC_DEVICE = "SR/MA/EPS-PLC-01"
PM_PLC_DOOR_ITLK = "/PC_PU_S07_01_DI"
PM_PLC_HVPS_PMV = "/PC_HVPS_RKA07C01_02_DO"
PM_PLC_HVPS_PMH = "/PC_HVPS_RKA07C01_01_DO"
PM_PLC_PMV = "PC_PU_RKA07C01_02_DO"
PM_PLC_PMH = "PC_PU_RKA07C01_01_DO"


class Pinger_Win(QtGui.QMainWindow):
    def __init__(self, param=None, parent=None):
        try:

            # Get graphical information
            QtGui.QWidget.__init__(self, parent)
            uipath = os.path.join(os.path.dirname(__file__),
                                "ui",
                                "pinger.ui")
            self.ui = uic.loadUi(uipath, self)
            
            self.devicelist = []
            self._pinger = param
            self.setWindowTitle(self._pinger+" Pinger Magnet")                       
            
            self.pmSetDevice()
            
            self.device = PyTango.DeviceProxy(self.dev)
            self.plc_device = PyTango.DeviceProxy(self.plcdev)

            # Sets device name
            self.ui.device_name.setText(self.dev)   

            self.connect(self.ui.onButton, QtCore.SIGNAL("clicked()"), self.pmOn)
            self.connect(self.ui.offButton, QtCore.SIGNAL("clicked()"), self.pmOff)
            self.connect(self.ui.applyButton, QtCore.SIGNAL("clicked()"), self.pmApply)
            self.connect(self.ui.resetButton, QtCore.SIGNAL("clicked()"), self.pmReset)                        
            self.connect(self.ui.reset_interlocks_button, QtCore.SIGNAL("clicked()"), self.pmResetInterlocks)
            self.connect(self.ui.clear_logs_button, QtCore.SIGNAL("clicked()"), self.pmClearLogs)
            self.connect(self.ui.taurusDisableVoltageDelayCheckBox, QtCore.SIGNAL("clicked()"), self.pmDisableVoltageDelay)
            
            # Menu Action
            QtCore.QObject.connect(self.ui.actionQuit, QtCore.SIGNAL("triggered()"), self.pmQuit)
            QtCore.QObject.connect(self.ui.actionOpen, QtCore.SIGNAL("triggered()"), self.pmOpen)
                        
            QtCore.QObject.connect(self.ui.scopeButton, QtCore.SIGNAL("clicked()"), self.pmStartScopeProcess)                                 
         
            ## Create the lists of attributes ########
            ## to connect     
            self.pmCreateLists() 

            ## Connect all the attributes #############
            self.connectedAttributeWidgets = []            
            for i,attr in enumerate(self._attrList):
                self.pmConnectAttribute(attr[0], attr[1])
                
            self.ui.status_value.setBgRole('state')                
                
            # Define ITLK LEDS colors
            self.ui.doorInterlockLed.setOffColor('GREEN')  
            self.ui.doorInterlockLed.setOnColor('RED')              
            self.ui.doorInterlockLed.setLedPatternName("leds_images256:led_{color}_on.png")
                                   
            self.ui.HVPSInterlockLed.setOnColor('RED')
            self.ui.HVPSInterlockLed.setOffColor('GREEN')                   
            self.ui.HVPSInterlockLed.setLedPatternName("leds_images256:led_{color}_on.png")
                       
            self.ui.PSInterlockLed.setOffColor('GREEN')  
            self.ui.PSInterlockLed.setOnColor('RED')              
            self.ui.PSInterlockLed.setLedPatternName("leds_images256:led_{color}_on.png")
                       
            # Initializes limits    
            self.ui.voltageSetPoint.setMinValue(MIN_VOLTAGE_VALUE)
            self.ui.voltageSetPoint.setMaxValue(MAX_VOLTAGE_VALUE)
                                                                       
        except Exception,e:
            print e
         
    def pmSetDevice(self):        
        if self._pinger =='VERTICAL-01':
            self.dev = PMV_01_DEVICE
            self.plcdev = PM_PLC_DEVICE
            self.hvps_att = PM_PLC_HVPS_PMV
            self.pson_att = PM_PLC_PMV
            self.psonotherpinger_att = PM_PLC_PMH
                        
        elif self._pinger =='HORIZONTAL-01':
            self.dev = PMH_01_DEVICE
            self.plcdev = PM_PLC_DEVICE
            self.hvps_att = PM_PLC_HVPS_PMH
            self.pson_att = PM_PLC_PMH
            self.psonotherpinger_att = PM_PLC_PMV                     
            
    def pmOn(self):
        try:           
            # Switch on relays        
            ps_state = self.plc_device.read_attribute(self.pson_att).value
            
            if ps_state:
                psotherpinger_state = self.plc_device.read_attribute(self.psonotherpinger_att).value
                if psotherpinger_state:
                    self.plc_device.write_attribute(self.pson_att, True)
                    text = 'PM Power supply On'
                    self.ui.Statusbox.append(text)                    
                    
                    # Reset pinger device
                    self.device.Init()
                    self.device.Reset()
                    text = 'PM device server reset'
                    self.ui.Statusbox.append(text)
                    
                    QtGui.QMessageBox.warning(self, 'Pinger Magnet',
                                          'The device also needs to be manually set to ON, to let remote control!!',
                                          QtGui.QMessageBox.Ok)
                else:
                    QtGui.QMessageBox.warning(self, 'Pinger Magnet',
                                              'There is already another Pinger Magnet device On.\nSwitch it off first, to avoid interferences.',
                                              QtGui.QMessageBox.Ok)
                     

            else:
                QtGui.QMessageBox.warning(self, 'Pinger Magnet', 'Device already On', QtGui.QMessageBox.Ok)                        
        except Exception, e:
            text = 'Failed to ON :: %s'%e
            self.ui.Statusbox.append(text)
            
    def pmOff(self):
        try:
            ps_state = self.plc_device.read_attribute(self.pson_att).value
            if not ps_state:            
                # Release the output first
                #self.device.Off()
                
                answer = QtGui.QMessageBox.critical( self, 'Pinger Magnet',
                                                  'Device is going to be set to Off.\n Are you sure to continue?',
                                                  QtGui.QMessageBox.Yes, 
                                                  QtGui.QMessageBox.No | QtGui.QMessageBox.Default)
                if answer == QtGui.QMessageBox.Yes:
                    try:
                        # Release the output
                        self.device.Off()
                        text = 'PM device set to Off'
                        self.ui.Statusbox.append(text)
                    except Exception, e:
                        text = 'PM device FAILED set to Off'
                        self.ui.Statusbox.append(text)                    
                                    
                    # C/M to avoid problems with the beam when swtich on the next time
                    try:
                        self.ui.voltageSetPoint.value = 0
                        self.device.write_attribute('VoltageSetPoint', self.ui.voltageSetPoint.value)                        
                        read = self.device.read_attribute('VoltageSetPoint').value            
                        text = 'Voltage set to %s Volts'%str(read)
                        self.ui.Statusbox.append(text)                
                    except Exception, e:
                        text = 'PM device FAILED set Voltage set Point to 0'
                        self.ui.Statusbox.append(text)
                                            
                    # MB on 12/11/14 due to the tango timeout problem 
                    # Reset pinger device
                    #self.device.Reset()
                    #text = 'PM device set to Off'
                    #self.ui.Statusbox.append(text)
                    
                    # Switch off relays
                    self.plc_device.write_attribute(self.pson_att, True)
                    text = 'Power supply Off'
                    self.ui.Statusbox.append(text)      
        except Exception, e:
            text = 'Failed to Off :: %s'%e
            self.ui.Statusbox.append(text)            
        
    def pmApply(self):
        try:
            # Forces a current of 60mA
            self.device.write_attribute('CurrentSetPoint', MAX_CURRENT_VALUE)
            read = self.device.read_attribute('CurrentSetPoint').value
            text = 'Current fixed to %s Amps'%str(read)
            self.ui.Statusbox.append(text)

            # Reads Voltage Set Point
            self.device.write_attribute('VoltageSetPoint', self.ui.voltageSetPoint.value)                        
            read = self.device.read_attribute('VoltageSetPoint').value            
            text = 'Voltage set to %s Volts'%str(read)
            self.ui.Statusbox.append(text)
            
            # Enable device server to load the output    
            self.device.On()
            text = 'PM device set to ON'
            self.ui.Statusbox.append(text)
        except:
            text = 'Failed to Load'
            self.ui.Statusbox.append(text)            
        
    def pmReset(self):
        try:
            self.device.Init()
        except Exception, e:
            text = 'PM Failed to Init'
            self.ui.Statusbox.append(text)       

        try:
            self.device.Reset()
            text = 'Reset OK'                   
            self.ui.Statusbox.append(text)
        except Exception, e:
            text = 'PM Failed to Reset'
            self.ui.Statusbox.append(text)       
            
    
    def pmResetInterlocks(self):
        try:
            # Set VoltageSetPoint to 0 to avoid damage the beam when the interlock dissapear
            # C/M to avoid problems with the beam when swtich on the next time
            self.ui.voltageSetPoint.value = 0
            self.device.write_attribute('VoltageSetPoint', self.ui.voltageSetPoint.value)
            read = self.device.read_attribute('VoltageSetPoint').value
            text = 'Voltage set to %s Volts'%str(read)
            self.ui.Statusbox.append(text)  

            self.device.Reset()
            text = 'Device Reset OK'
            self.ui.Statusbox.append(text)  
            
            # Reset PLC device        
            self.plc_device.write_attribute("PLC_CONFIG_RESET", int(1))
            text = 'interlock reset OK'
            self.ui.Statusbox.append(text)
        except:
            text = 'Failed to reset interlock'
            self.ui.Statusbox.append(text)   
        
    def pmQuit(self):
        print 'Hasta la proxima...baby!!!'
        self.close()
        
    def pmOpen(self):
        cmd ='python gui_pinger.py'
        os.system(cmd)    
        
    def pmClearLogs(self):
        self.ui.Statusbox.clear()
        
    def pmDisableVoltageDelay(self):
        pass
#         if self.ui.taurusDisableVoltageDelayCheckBox.checkState():
#             self.ui.voltageSetPoint.setEnabled(False)
#             self.ui.voltageReadback.setEnabled(False)
#         else:
#             self.ui.voltageSetPoint.setEnabled(True)
#             self.ui.voltageReadback.setEnabled(True)
            
    def pmConnectAttribute(self, widget, attr):
        # Connect to tango attributes
        try:
            widget.setModel(attr)
            self.connectedAttributeWidgets += [widget]
        except Exception, e:
            print "Error in connectAttribute::%s ==> %s"%(attr, e) 

    def pmCreateLists(self):
        # Initializes list of attributes
        self._attrList = [(self.ui.taurusLed_status, self.dev+'/State'),
                          (self.ui.status_value, self.dev+'/Status'),
                          (self.ui.voltageReadback, self.dev+'/Voltage'),
                          (self.ui.voltageSetPoint, self.dev+'/VoltageSetPoint'),
                          (self.ui.doorInterlockLed, self.plcdev+PM_PLC_DOOR_ITLK),
                          (self.ui.HVPSInterlockLed, self.plcdev+self.hvps_att),
                          (self.ui.PSInterlockLed, self.plcdev+'/'+self.pson_att),
                          (self.ui.voltageDelay, self.dev+'/VoltageDelay'),
                          (self.ui.bunchDelay, self.dev+'/BunchDelay'),
                          (self.ui.totalDelay, self.dev+'/TotalDelay'),
                          (self.ui.taurusDisableVoltageDelayCheckBox,self.dev+'/DisableVoltageDelay')]
        
    def pmStartScopeProcess(self):
        try:
            self.qpro = QtCore.QProcess(self)
            #self.qpro.start('vncviewer scodisr0701')
            self.qpro.start('javaws http://scodisr0701/scodisr0701_2.jnlp') # To test for future...scope controls
            if self.qpro.waitForFinished(5000) == True:
                text = 'Scope started'
            else:
                text = 'Error Starting Scope process'
        except Exception,e:
            text = 'Error Starting Scope process', str(e)
        self.ui.Statusbox.append(text)                       
                                           
def main():      
    import os
    print fandango.get_tango_host()
    tangodbName = fandango.get_tango_host()
    
    app= QtGui.QApplication(sys.argv)    
 
    total_args = len(sys.argv)
    pingerSelected =[]

    if len(sys.argv) == 2:
        pingerSelected = sys.argv[1]

    if tangodbName is not None and tangodbName.startswith("alba03"):
        valid_pingers = ('VERTICAL-01','HORIZONTAL-01')
    else:
        valid_pingers = ()
    #if (pingerSelected is None) or (pingerSelected.upper() not in valid_pingers):
    if (pingerSelected == []):
        pingerSelected, ok = QtGui.QInputDialog.getItem(None, "Choose pinger magnet", "Pinger Magnet", valid_pingers)
        if not ok:
            sys.exit(-1)
        else:
            pingerSelected = str(pingerSelected)

    if pingerSelected:   
        task = Pinger_Win(pingerSelected)
        task.show()
    else:
        print "** No Pinger Magnet selected **"
        print "Check proper TANGO host or use it with argument:"
        print "pingermagnet \tvertical-01 or horizontal-01\n"
        sys.exit(-1)        

    sys.exit(app.exec_())
               
if __name__ == "__main__":
    main()
