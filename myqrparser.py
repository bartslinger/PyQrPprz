#!/usr/bin/env python
import socket
import getopt
import sys
import time
import threading
import logging
import signal
from os import path, getenv
from qrtools import QR


# if PAPARAZZI_SRC not set, then assume the tree containing this
# file is a reasonable substitute
PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '../../../../')))
sys.path.append(PPRZ_SRC + "/sw/lib/python")

PPRZ_HOME = getenv("PAPARAZZI_HOME", PPRZ_SRC)


from ivy_msg_interface import IvyMessagesInterface
from pprz_msg.message import PprzMessage

def Usage(scmd):
    lpathitem = scmd.split('/')
    fmt = '''Usage: %s [-h | --help] [-a AC_ID | --ac_id=AC_ID]
where
\t-h | --help print this message
\t-a AC_ID | --ac_id=AC_ID where AC_ID is an aircraft ID to use for downloading log data
\t-w WAYPOINT_ID | --waypoint_id=WAYPOINT_ID where WAYPOINT_ID is the waypoint of which the location is changed according to the QR code presented
'''
    print(fmt % lpathitem[-1])

def GetOptions():
	options = {'ac_id':[], 'waypoint_id':[]}
	try:
		optlist, left_args = getopt.getopt(sys.argv[1:],'h:a:w:', ['help', 'ac_id=', 'waypoint_id'])
	except getopt.GetoptError:
        # print help information and exit:
		Usage(sys.argv[0])
		sys.exit(2)
	for o, a in optlist:
		if o in ("-h", "--help"):
			Usage(sys.argv[0])
			sys.exit()
		elif o in ("-a", "--ac_id"):
			options['ac_id'].append(int(a))
		elif o in ("-w", "--waypoint_id"):
			options['waypoint_id'].append(int(a))

	return options

myCode = QR()


class myQRParser():
	def signal_handler(self, signal, frame):
			print('You pressed Ctrl+C!')
			self.interface.shutdown()
			sys.exit(0)

	def myCrapThread(self):
		time.sleep(1)
		myCode.decode_webcam(callback=self.codeRecognized, device='/dev/video0')
		#print('Finished, please ctrl+c')
		self.interface.shutdown()
		sys.exit(0)

	def __init__(self, ac_id, waypoint_id):
		self.ac_id = ac_id[0]
		self.waypoint_id = waypoint_id[0]
		self.interface = IvyMessagesInterface(self, self.emptyFun)
				
		t = threading.Thread(target=self.myCrapThread)
		t.start()

		signal.signal(signal.SIGINT, self.signal_handler)
		print('Press Ctrl+C')
		signal.pause()
		
		self.interface.shutdown()

	def emptyFun(ac_id, msg):
		print "Never"

	def codeRecognized (self, data):
		print data
		if data == '1':
			coords = 1
			print "Dropzone 1"
		elif data == '2':
			coords = 2
			print "Dropzone 2"
		elif data == '3':
			coords = 3
			print "Dropzone 3"
		else:
			print data
			return
		print('Going to: ', coords)
		pprzmsg = PprzMessage("ground", "DL_SETTING")
		pprzmsg.set_values([self.ac_id, self.waypoint_id, coords])
		self.interface.send(pprzmsg)
		#pprzmsg.set_values([self.ac_id, (self.waypoint_id+1), coords[0], coords[1], 10])
		#self.interface.send(pprzmsg)

	def __call__(a, b, c):
		print ""



def main():
	# Aircraft ID should be supplied
	options = GetOptions()
	if not options['ac_id']:
	    Usage(sys.argv[0])
	    sys.exit("Error: Please specify at least one aircraft ID.")
	if not options['waypoint_id']:
		Usage(sys.argv[0])
		sys.exit("Error: Specify the waypoint to fly to.")

	parser = myQRParser(options['ac_id'], options['waypoint_id'])

if __name__ == '__main__':
	main()
