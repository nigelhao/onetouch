#Function that only applies to linux - Debian
#As the function here rely on a template based on linux
#TODO: Check if the function here will work on other distro such as unbuntu, redhat, centos 
#Author: Nigel Chen Chin Hao

import puppet_common

#Insert the configuration to the pupper server, this is the template
#Puppet server will then create the virtual machine base on the template provided
def configuration(m):
    s = open("./puppet/template/vsphere_vm/vsphere_vm_deb_template.txt").read()
    s = s.replace('VM_NAME', m.vmName)
    s = s.replace('HOSTNAME', m.hostname)
    s = s.replace('OS', 'Debian')
    s = s.replace('MEMORY', m.memory)
    s = s.replace('VCPU', m.cpu)
    s = s.replace('ROOT_PASSWORD', 'Skills39')
    s = s.replace('USERNAME', 'Administrator')
    s = s.replace('USER_PASSWORD', '$kills39')
    filename = "./puppet/new_nodes/%s_conf.txt" % (m.vmName)
    f = open(filename, "w" )
    f.write(s)
    f.close()
    puppet_common.executeConfig(m.vmName)

#Manifest, takes the infrastructure as a code, so by configuring the manifest
#Virtual machine will pull the manifest and configure it accordingly to the manifest
def manifest(m):
    s = open("./puppet/template/manifest/manifest_deb_base.txt").read()
    s = s.replace('HOSTNAME', m.hostname)
    s = s.replace('IP_ADDRESS', m.address)
    s = s.replace('NETMASK', m.netmask)
    s = s.replace('GATEWAY', m.gateway)
    s = s.replace('DNS_SERVER', m.dns)
    filename = "./puppet/new_nodes/%s_manifest.txt" % (m.vmName)
    f = open(filename, "w" )
    f.write(s)
    f.close()
    puppet_common.executeManifest(m.vmName)
