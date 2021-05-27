#!/usr/bin/python3

from bluepy.btle import Scanner, DefaultDelegate
import sys


def print_help():
    print("Usage:")
    print("  " + sys.argv[0] + " -h or --help = print this help")
    print("  " + sys.argv[0] + " -s = scan for Bluetooth IDs")
    print("  " + sys.argv[0] + " -s 10 = scan for Bluetooth IDs for 10 seconds")
    print("  " + sys.argv[0] + " -f xx:xx:xx:xx = continuously scan for this device")


def perform_scan(scantime):
    class ScanDelegate(DefaultDelegate):
            def __init__(self):
                DefaultDelegate.__init__(self)

            def handleDiscovery(self, dev, isNewDev, isNewData):
                if isNewDev:
                    print("  [+] Discovered device: " + dev.addr)
                elif isNewData:
                    print("  [+] Received new data from: " + dev.addr)

    print("[*] Scanning for devices...")
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(scantime)

    print("[*] Scan complete\n")
    print("[*] Gathering device data...")
    for dev in devices:
        print ("[+] Device: " + dev.addr + " RSSI:" +  str(dev.rssi) + "dB")
        for (adtype, desc, value) in dev.getScanData():
            print("    " + desc + " : " + value)


def request_rssi(btid, scantime=3):
    scanner = Scanner()
    devices = scanner.scan(scantime)
    myrssi = None
    for dev in devices:
        if(dev.addr == btid):
            myrssi = dev.rssi

    return myrssi



def perform_follow(btid):
    print("[+] Following " + btid)
    myrssi = request_rssi(btid)
    if(myrssi == None):
        print("[-] Device is out of range or switched off!")
        inRange = False
    else:
        print("[+] Device is in range!")
        inRange = True

    while(True):
        myrssi = request_rssi(btid)

        if(inRange == True):
            if(myrssi == None):
                inRange = False
                print("[-] Device has gone out of range or been switched off!")
            else:
                print("  - RSSI = " + str(myrssi) + "dB     ", end='\r')
        else:
            if(myrssi != None):
                inRange = True
                print("[+] Device is now in range!")
                print("  - RSSI = " + str(myrssi) + "dB     ", end='\r')



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
