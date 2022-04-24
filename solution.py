
from socket import *
import socket
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 1
# The packet that we shall send to each router along the path is the ICMP echo
# request packet, which is exactly what we had used in the ICMP ping exercise.
# We shall use the same packet that we built in the Ping exercise

def checksum(string):
# In this function we make the checksum of our packet
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def build_packet():
    myChecksum = 0
    unique_ID = os.getpid() & 0xffff
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, unique_ID, 1)
    data = struct.pack("d", time.time())
    myChecksum = checksum(header + data)
    if sys.platform == 'darwin':
        myChecksum = socket.htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, unique_ID, 1)
    packet = header + data
    return packet

def get_route(hostname):
    timeLeft = TIMEOUT
    tracelist1 = []
    tracelist2 = []
    destAddr = socket.gethostbyname(hostname)
    for ttl in range(1, MAX_HOPS):
        for tries in range(TRIES):
            tracelist2.append(tracelist1)
            icmp = socket.getprotobyname("icmp")
            mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

            mySocket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)
            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t = time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)
                if whatReady[0] == []:
                    tracelist1.append("* * * Request timed out.")
                    tracelist1.append(whatReady[0])
                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft = timeLeft - howLongInSelect
                if timeLeft <= 0:
                    tracelist1.append("* * * Request timed out.")
                    tracelist1.append(tracelist1)

            except socket.timeout:
                continue

            else:
                icmpHeader = recvPacket[20:28]
                types, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
                try:
                    theName = gethostbyaddr(destAddr)[0]
                    nameSplit = theName.split(".")[0]
                    if theName == nameSplit:
                        theName = " "
                    #Fill in end
                except herror:
                    nameSplit = destAddr
                    theName = "hostname not returnable"
                    return theName

                if types == 11:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    tracelist1.append((str(ttl), str(round((timeReceived-t)*1000)) + "ms", addr[0], get_route(addr[0])))

                elif types == 3:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    tracelist1.append((str(ttl), str(round((timeReceived - t) * 1000)) + "ms", addr[0], get_route(addr[0])))
                elif types == 0:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    tracelist1.append("error")
                    print(tracelist2)
                    tracelist1.clear()
                    return tracelist2
                else:
                    tracelist1.append("error")
                    break
            finally:
                mySocket.close()

if __name__ == '__main__':
    get_route("google.co.il")