#!/usr/bin/python3

import time
import sys
import bluetooth
import bluetooth._bluetooth as bt
import struct
import array
import fcntl


class BluetoothRSSI(object):
    """Object class for getting the RSSI value of a Bluetooth address."""

    def __init__(self, addr):
        self.addr = addr
        self.hci_sock = bt.hci_open_dev()
        self.hci_fd = self.hci_sock.fileno()
        self.bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self.bt_sock.settimeout(10)
        self.closed = False
        self.connected = False
        self.cmd_pkt = None

    def prep_cmd_pkt(self):
        """Prepare the command packet for requesting RSSI."""
        reqstr = struct.pack(
            b'6sB17s', bt.str2ba(self.addr), bt.ACL_LINK, b'\0' * 17)
        request = array.array('b', reqstr)
        handle = fcntl.ioctl(self.hci_fd, bt.HCIGETCONNINFO, request, 1)
        handle = struct.unpack(b'8xH14x', request.tobytes())[0]
        self.cmd_pkt = struct.pack('H', handle)

    def connect(self):
        """Connect to the Bluetooth device."""
        # Connecting via PSM 1 - Service Discovery
        self.bt_sock.connect_ex((self.addr, 1))
        self.connected = True

    def close(self):
        """Close the bluetooth socket."""
        self.bt_sock.close()
        self.hci_sock.close()
        self.closed = True

    def request_rssi(self):
        """Request the current RSSI value.
        @return: The RSSI value or None if the device connection fails
                 (i.e. the device is not in range).
        """
        try:
            # If socket is closed, return nothing
            if self.closed:
                return None
            # Only do connection if not already connected
            if not self.connected:
                self.connect()
            # Command packet prepared each iteration to allow disconnect to trigger IOError
            self.prep_cmd_pkt()
            # Send command to request RSSI
            rssi = bt.hci_send_req(
                self.hci_sock, bt.OGF_STATUS_PARAM,
                bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, self.cmd_pkt)
            rssi = struct.unpack('b', rssi[3].to_bytes(1, 'big'))
            return rssi
        except IOError:
            # Happens if connection fails (e.g. device is not in range)
            self.connected = False
            # Socket recreated to allow device to successfully reconnect
            self.bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            return None



def print_help():
    print("Usage:")
    print("  " + sys.argv[0] + " -h or --help = print this help")
    print("  " + sys.argv[0] + " -s = scan for Bluetooth IDs")
    print("  " + sys.argv[0] + " -s 10 = scan for Bluetooth IDs for 10 seconds")
    print("  " + sys.argv[0] + " -f xx:xx:xx:xx = continuously scan for this device")

def perform_scan(scantime):
    nearby_devices = bluetooth.discover_devices(duration=scantime, lookup_names=True)

    if(len(nearby_devices) > 0):
        print("[+] Found " + str(len(nearby_devices)) + " devices in range!")
        for (dev_addr,readable_name) in nearby_devices:
            print("  [+] " + dev_addr + " " + readable_name)
    else:
        print("[-] No discoverable devices in range!")

def perform_follow(btaddr):
    print("[*] Following " + btaddr)
    btrssi = BluetoothRSSI(addr=btaddr)

    myrssi = btrssi.request_rssi()
    if(myrssi == None):
        print("[-] Device is out of range or switched off!")
        inRange = False
    else:
        print("[+] Device is in range!")
        inRange = True

    while(True):
        myrssi = btrssi.request_rssi()

        if(inRange == True):
            if(myrssi == None):
                inRange = False
                print("[-] Device has gone out of range or been switched off!")
            else:
                print("  - RSSI = " + str(myrssi[0]) + "dB     ", end='\r')
        else:
            if(myrssi != None):
                inRange = True
                print("[+] Device is now in range!")
                print("  - RSSI = " + str(myrssi[0]) + "dB     ", end='\r')

        time.sleep(1)

if(len(sys.argv) == 1):
    print_help()
else:
    if(sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print_help()
    elif(sys.argv[1] == "-s"):
        if(len(sys.argv) == 3):
            perform_scan(int(sys.argv[2]))
        else:
            perform_scan(10)
    elif(sys.argv[1] == "-f" and len(sys.argv) == 3):
        perform_follow(sys.argv[2])
    else:
        print_help()
