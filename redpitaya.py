###############################################################################
#    pyrpl - DSP servo controller for quantum optics with the RedPitaya
#    Copyright (C) 2014-2016  Leonhard Neuhaus  (neuhaus@spectro.jussieu.fr)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################


from sshshell import SSHshell
from time import sleep
from matplotlib import pyplot
import math
import numpy
import numpy as np
import os
from time import sleep
import socket
import rpyc
from pylab import *
import pandas

import monitor_client
import redpitaya_modules as rp

class RedPitaya(SSHshell):

    def __init__(self,hostname='10.214.1.23', port=2222,
                 user='root', password='root',
                 verbose=False, autostart=True, reloadfpga=True,
                 filename=None, dirname=None,
                 leds_off=True, frequency_correction=1.0):
        self.license()
        self.serverdirname = "//opt//rplockbox//"
        self.serverrunning=False
        self.hostname = hostname
        self.port = port
        self.conn = None
        self.client = None
        self.frequency_correction = frequency_correction
        self.leds_off = leds_off
        if filename is None:
            self.filename = 'FPGA//red_pitaya.bin'
        else:
            self.filename = filename
        self.subdirname,self.filename = os.path.split(self.filename)
        if dirname is None:
            try:
                import pyrpl.redpitaya as pyrp
                self.dirname = os.path.dirname(pyrp.__file__)
            except:
                self.dirname = os.getcwd()
            else:
                self.dirname = dirname
        super(RedPitaya,self).__init__(hostname=hostname,user=user,
                                       password=password,verbose=verbose)
        if reloadfpga:
            self.update_fpga()
        if autostart:
            self.start()

    def switch_led(self,gpiopin=0,state=False):
        self.ask("echo "+str(gpiopin)+" > /sys/class/gpio/export")
        sleep(self.delay)
        self.ask("echo out > /sys/class/gpio/gpio"+str(gpiopin)+"/direction")
        sleep(self.delay)
        if state:
            state = "1"
        else:
            state = "0"
        self.ask("echo "+state+" > /sys/class/gpio/gpio"+str(gpiopin)+"/value")
        sleep(self.delay)

    def compile_lib(self):
        self.end()
        os.chdir(os.join(self.dirname,"monitor_server"))
        os.system("make all")
        self.ask('rw')
        sleep(self.delay)
        self.scp.put('monitor_server',self.serverdirname)
        sleep(self.delay)
        self.ask('chmod 755 ./monitor_server')
        self.ask('ro')

    def update_fpga(self,filename = None):
        if filename is None:
            filename = self.filename
        self.end()
        os.chdir(os.join(self.dirname,self.subdirname))
        self.ask('rw')
        sleep(self.delay)
        self.ask('mkdir '+self.serverdirname)
        sleep(self.delay)
        self.scp.put(filename,self.serverdirname)
        sleep(self.delay)
        self.ask('killall nginx')
        self.ask('cat '+os.join(self.serverdirname,filename)+' > //dev//xdevcfg')
        self.ask("nginx -p //opt//www//")
        sleep(self.delay)
        self.ask('ro')

    def startserver(self):
        if self.serverrunning:
            self.endserver()
        os.chdir(os.join(self.dirname,"monitor_server//"))
        self.ask('rw')
        sleep(self.delay)
        self.ask('mkdir '+self.serverdirname)
        sleep(self.delay)
        self.scp.put('monitor_server',self.serverdirname)
        self.ask("cd "+self.serverdirname)
        self.ask('chmod 755 ./monitor_server')
        self.ask('ro')
        self.ask("./monitor_server "+str(self.port))
        self.serverrunning=True

    def endserver(self):
        self.ask('\x03')
        if 'pitaya' in self.ask():
            print 'Properly shut down the rpyc server!'
        self.serverrunning = False

    def killserver(self):
        return self.ask('killall monitor_server')

    def startclient(self):
        self.client = monitor_client.MonitorClient(self.hostname, self.port, restartserver=self.restartserver)
        self.hk = rp.HK(self.client)
        self.ams = rp.AMS(self.client)
        self.scope = rp.Scope(self.client)
        self.pid0= rp.Pid(self.client, number=0)
        self.pid1= rp.Pid(self.client, number=1)
        self.pid2= rp.Pid(self.client, number=2)
        self.pid3= rp.Pid(self.client, number=3)
        self.iir = rp.IIR(self.client, number=4)
        self.iq0 = rp.IQ(self.client, number=5)
        self.iq1 = rp.IQ(self.client, number=6)
        self.iq2 = rp.IQ(self.client, number=7)
        self.asg1 = rp.ASG(self.client, channel='A')
        self.asg2 = rp.ASG(self.client, channel='B')
        temp = float(self.ams.temp)
        print "Client started. FPGA temperature is",temp,"degrees"

    def endclient(self):
        del self.client
        self.client = None

    def start(self):
        self.killserver()
        if self.leds_off:
            self.switch_led(gpiopin=0, state=False)
            self.switch_led(gpiopin=7, state=False)
        self.startserver()
        sleep(self.delay)
        self.startclient()

    def end(self):
        self.endserver()
        self.endclient()
        self.killserver()

    def __del__(self):
        self.end()
        self.ssh.close()

    def restart(self):
        self.end()
        self.start()

    def restartserver(self):
        """restart the server. usually executed when client encounters an error"""
        self.endserver()
        self.ask("./monitor_server "+str(self.port))
        self.serverrunning=True
        print "Restarted monitor_server"

    def license(self):
        print """    pyrpl  Copyright (C) 2014-2016  Leonhard Neuhaus
                This program comes with ABSOLUTELY NO WARRANTY; for details read the file
                "LICENSE" in the source directory. This is free software, and you are
                welcome to redistribute it under certain conditions; read the file
                "LICENSE" in the source directory for details."""

