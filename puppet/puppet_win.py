#Function that only applies to Windows
#As the function here rely on a template based on Windows
#Author: Nigel Chen Chin Hao

import puppet_common
import os

#Insert the configuration to the pupper server, this is the template
#Puppet server will then create the virtual machine base on the template provided
def configuration(m):
    s = open("./puppet/template/vsphere_vm/vsphere_vm_win_template.txt").read()
    s = s.replace('VM_NAME', m.vmName)
    s = s.replace('OS', 'Windows')
    s = s.replace('MEMORY', m.memory)
    s = s.replace('VCPU', m.cpu)
    filename = "./puppet/new_nodes/%s_conf.txt" % (m.vmName)
    f = open(filename, "w" )
    f.write(s)
    f.close()
    puppet_common.executeConfig(m.vmName)

#Manifest, takes the infrastructure as a code, so by configuring the manifest
#Virtual machine will pull the manifest and configure it accordingly to the manifest
#Due to the inflexibility of windows, manifest configuration will be split into 2 portion
#Pre-manifest: Insert all the necessary data inserted by the technician
#Post-manifest: Tag the hostname with the corresponding file with the configuration and then execute it
def preManifest(m):
    s = open("./puppet/template/manifest/manifest_win_base.txt").read()
    s = s.replace('IP_ADDRESS', m.address)
    s = s.replace('NETMASK', m.netmask)
    s = s.replace('GATEWAY', m.gateway)
    s = s.replace('DNS_SERVER', m.dns)
    filename = "./puppet/new_nodes/%s_preManifest.txt" % (m.vmName)
    f = open(filename, "w" )
    f.write(s)
    f.close()

def postManifest(vmName, hostname):
    filename_s = "./puppet/new_nodes/%s_preManifest.txt" % (vmName) 
    s = open(filename_s).read()
    s = s.replace('HOSTNAME', hostname)
    filename_f = "./puppet/new_nodes/%s_manifest.txt" % (vmName)
    f = open(filename_f, "w" )
    f.write(s)
    f.close()
    puppet_common.executeManifest(vmName)

#Access to puppet server obtain the virtual machine name with the only known windows uuid
def grabVmName(uuid):
    #TODO: Change this to the api form instead of using OS level command
    return os.popen("ssh root@puppet.fyp.nyp puppet resource vsphere_vm | grep %s -B100 | grep vsphere_vm | cut -d \"'\" -f2 | rev | cut -d / -f1 | rev" % (uuid)).read().strip('\n')

#Format UUI of windows so that it is able to find the UUID on puppet enterprise
def formatUUID(unformatUUID):
    unformatArrUUID = unformatUUID.lstrip("VMware-").replace('-', ' ').split(' ')
    formatUUID = ""
    dashCount = 0
    for u in unformatArrUUID:
        if dashCount == 4 or dashCount == 6 or dashCount == 8 or dashCount == 10:
            formatUUID += '-'
        formatUUID += u
        dashCount += 1
    return formatUUID


