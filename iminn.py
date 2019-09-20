#######################################################################
#
#  IMinn- Bluetooth Presence Sensor for Raspberry Zero W
#  Alpha Ver. 1 Alpha
#
#  By Orman Beckles aka The Hi Tech Nomad - 2019
#  Youtube.com/TheHITechNomad
#
####################################################################### 
import requests
import fcntl
import struct
import array
import bluetooth
import bluetooth._bluetooth as bt
import RPi.GPIO as GPIO
import time
import os
import datetime

def bluetooth_rssi(addr):
    # Open hci socket
    hci_sock = bt.hci_open_dev()
    hci_fd = hci_sock.fileno()

    # Connect to device (to whatever you like)
    bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    bt_sock.settimeout(10)
    result = bt_sock.connect_ex((addr, 1))	# PSM 1 - Service Discovery

    try:
        # Get ConnInfo
        reqstr = struct.pack("6sB17s", bt.str2ba(addr), bt.ACL_LINK, "\0" * 17)
        request = array.array("c", reqstr )
        handle = fcntl.ioctl(hci_fd, bt.HCIGETCONNINFO, request, 1)
        handle = struct.unpack("8xH14x", request.tostring())[0]

        # Get RSSI
        cmd_pkt=struct.pack('H', handle)
        rssi = bt.hci_send_req(hci_sock, bt.OGF_STATUS_PARAM,
                     bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, cmd_pkt)
        rssi = struct.unpack('b', rssi[3])[0]

        # Close sockets
        bt_sock.close()
        hci_sock.close()

        return rssi

    except:
        return None



far = True
far_count = 0


# assume device is initially far away
rssi = -255
rssi_prev1 = -255
rssi_prev2 = -255
test_if_really_here = False
near_cmd = 'br -n 1'
far_cmd = 'br -f 1'
trigger_level=-1
cooldown=0
in_room_rssi_goal=-3
still_in_room=-20
exit_task=0
in_the_area=0
enter_room_event = "https://maker.ifttt.com/trigger/iminn_dollhouse/with/key/yourkey"
leave_room_event = "https://maker.ifttt.com/trigger/imout_dollhouse/with/key/yourkey"

# Enter the MAC address of your watch
target_addr = '00:00:00:00:00:00'

debug = 1

while True:
    # get rssi reading for address
    rssi = bluetooth_rssi(target_addr)

    if debug:
        print ("Starting from the top..")
	print datetime.datetime.now(), "rssi=",rssi, "rssi_prev1=",rssi_prev1, "rssi_prev2",rssi_prev2, "far=",far, "Far count=",far_count,"\n"

    if rssi==None: # The Raspberry Pi can't see the device at all
	if debug:
		print "I can't see the device at all rssi=",rssi,"\n"
		print "cooldown=",cooldown,"Exit task=",exit_task
	if cooldown==1: # This will only run once, when the device leaves the area
		if debug:
			print "Running exit event"
		requests.post(leave_room_event)
		exit_task = 1 # This prevents the exit task from running over and over again
		cooldown=0

    else:

	if cooldown == 0: #If cooldown means you are still around but won't keep running trigger request
		if debug:
			print "cool down loop"
			print rssi
			print trigger_level
		i = 1 
		while i < 30:

			if rssi<trigger_level:
				if debug:
					print "Level change New high level",trigger_level,rssi
				trigger_level=rssi
			else:
				print "Current trigger_level=",trigger_level,"in room goal=",in_room_rssi_goal,"rssi=",rssi,"Cool down=",cooldown,"i=",i
				trigger_level=rssi
			i += 1
		
		if trigger_level > in_room_rssi_goal:
			print  ("Trigger Level has been met",trigger_level)
			if debug:
				print("Sending enter room trigger to ifttt")
			requests.post(enter_room_event)
			cooldown= 1
			trigger_level=0
			print "break: cooldown=",cooldown

		else:
			print ("level not meet")
	#else:
	#	if debug:
	#		print ("cool down: Exit Task=",exit_task,"RSSI=",rssi)
	#	if still_in_room < rssi:
	#		print ("You probally left the room")
	#		#rssi=None
	#		cooldown=1
	#	else:
	#		if debug:
	#			print ("I think you are still in the room")

	if debug:
		print "Starting over...and cooldown=",cooldown,"exit_task=",exit_task



    rssi = rssi_prev1
    rssi_prev1  = rssi_prev2
