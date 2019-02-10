#Object for easier management
#Author: Nigel Chen Chin Hao

class Machine:
    def __init__(self, vmName, cpu, memory, osType, address, netmask, gateway, dns, hostname):
        self.vmName = vmName
        self.cpu = cpu
        self.memory = memory
        self.osType = osType
        self.address = address
        self.netmask = netmask 
        self.gateway = gateway
        self.dns = dns
        self.hostname = hostname #Currently not working on windows 
        #TODO: Find some way to able to change the hostname for windows, good luck

class Machine_Networking:
    def __init__(self, rid, address, netmask, gateway, dns):
        self.rid = rid
        self.address = address
        self.netmask = netmask 
        self.gateway = gateway
        self.dns = dns

