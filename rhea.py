# -*- coding: utf-8 -*-
"""
Created on Wed Oct 19 18:57:24 2022

@author: Xinyu Hu xh1165@g.rit.edu
"""

import random
from socket import socket, AF_INET, SOCK_DGRAM
import struct
import select
import time
#router configuration
#* queeg: 129.21.30.37/24
#* comet: 129.21.34.80/24
#* rhea: 129.21.37.49/24
#* glados: 129.21.22.196/24
# subnet mask: 255.255.255.0


queeg = "129.21.30.37"
comet="129.21.34.80"
ME="129.21.37.49"#I am rhea
glados="129.21.22.196"
mask="/24"
PORT = 5050
neighbors = set()
routing_table = {}
CONNECTED = set()
NEW_CONNECTIONS = set()
neighbors.add(comet)#comet
neighbors.add(glados)#glados
def createRoutingTable():
#    dis_queeg_to_comet = input('Set distance for queeg to comet: ')
#    dis_queeg_to_glados = input('Set distance for queeg to comet: ')
#TODO: for some reason asking for input doesn't work so for now I am going to use random
    dis_rhea_to_comet=7
    dis_rhea_to_glados=4
    routing_table.update({comet:[mask,comet,dis_rhea_to_comet]})#format: dest, subnetmask, nexthop, dist
    routing_table.update({glados:[mask,glados,dis_rhea_to_glados]})#format: dest, subnetmask, nexthop, dist
    #routing_table.update({rhea})
    return

#make the routing_table into packed binary data
def putInfoIntoBinary():
    binary_r_t = bytearray()
#    type = 0
#    binary_r_t.extend(type.to_bytes(1, byteorder='big'))
    for dest, data in routing_table.items():
        #destination into binary
        a, b, c, d = tuple(map(lambda x: int(x), dest.split(".")))
        #distance itself
        dist = int(data[-1])
        binary_r_t_bytes = struct.pack("BBBBB", a, b, c, d, dist)
        binary_r_t.extend(binary_r_t_bytes)
    return binary_r_t

#update the routing table
def updateRoutingTable(binary_r_t, neighbor_ip):

    binary_r_t = binary_r_t[1:]
    update = False
    
    
    for index in range(0, len(binary_r_t), 5):
#        if len(binary_r_t) < 5:
#            break
        temp = binary_r_t[index:index+5]
        #make the buffer for unpack
        #reform the routing table from binary form
        routing_table_entries_part = struct.unpack('BBBBB', temp)
        routing_table_entries_part = list(map(lambda x: str(x), routing_table_entries_part))
        ip = ".".join(routing_table_entries_part[:4])
        dist = int(routing_table_entries_part[4])

        if ip in routing_table:
            if routing_table[ip][-1] > int(dist + routing_table[neighbor_ip][-1]):
                #found a closer route
                routing_table[ip] = [
                    (dist + int(routing_table[neighbor_ip][-1])), routing_table[neighbor_ip][-2]]
                #change to that route
                update = True
                #use this to trigger update for all router
        elif ip == ME:
            continue
        else:
            routing_table[ip] = [
                (dist + int(routing_table[neighbor_ip][-1])), neighbor_ip]
            update = True

    return update

#send the updated routing table
def sendRoutingTable(ip):

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.connect((ME, PORT))
    binary_r_t = putInfoIntoBinary()

    host_addr = ip.split(".")[-1]#since net mask is 255.255.255.0, the last part of ip address is needed

    sock.sendto(binary_r_t, (ip, PORT+int(host_addr)))
    sock.close()


#print routing table
def printRoutingTable():
    #format: dest, subnetmask, nexthop, dist
    print('{:^20}{:^10}{:^10}{:^20}'.format("Destination", "Subnetmask", "NextHop","Distance"))
    for ip in routing_table:
        print('{:^20}{:^10}{:^10}{:^20}'.format(
            ip, routing_table[ip][0], routing_table[ip][1], routing_table[ip][2]))

inputs=[]
connected = set()
new_connections = set()
def main():
    #start
    print("Time x ", time.strftime("%H:%M:%S"), ", rhea", ME)
    #set up
    createRoutingTable()
    with socket(AF_INET, SOCK_DGRAM) as server:
        print("Time x ",time.strftime("%H:%M:%S"),f', Connecting to rhea {ME}:5050')
        server.connect((ME, PORT))
        inputs=[server]
        print("Time x ",time.strftime("%H:%M:%S"),f', Listening on rhea {ME}:5050')
#        time.sleep(random.randint(1,10))
        for neib in neighbors:
            sendRoutingTable(neib)
        printRoutingTable()
        while inputs:
            #I looked at the example from https://pythontic.com/modules/select/select
            readList, writeList, exceptionList = select.select(inputs, [], [], 10)
            update=False
            #init the boolean to decide update on routing table
            for read in readList:
               recv, addr = server.recvfrom(1024)
               #I looked at the example from https://pythontic.com/modules/socket/recvfrom
               if recv:
                   update=updateRoutingTable(recv,addr[0])
                   if update:
                       #time.sleep(random.randint(1, 10))
                       #there is routing table update, show it
                       print(time.strftime('%H:%M:%S'),f", There's update from {addr[0]}")
                       printRoutingTable()
            if update:
                #there's an update here, make everyone update
                for neib in neighbors:
                    sendRoutingTable(neib)
            #make sure if there is new connection, add them to the routing table
            for i in inputs:
                connected.add(i.getsockname()[0])
            new_connections = neighbors - connected
            for neib in new_connections:
                sendRoutingTable(neib)
if __name__ == "__main__":
    main()