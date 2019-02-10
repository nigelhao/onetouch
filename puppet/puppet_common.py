#A common function that help assist in deploy, configure and transfer files to the pupper server
#Author: Nigel Chen Chin Hao

import time
import api

#Transfer configuration file to puppet server and then execute it via SSH
def executeConfig(vmName):
    api.ftpUpload("./puppet/new_nodes/%s_conf.txt" % (vmName), "/puppet/new_nodes/%s.pp" % (vmName))
    api.sshCommand("puppet apply /puppet/new_nodes/%s.pp &" % (vmName))
    api.removeLocalFile("./puppet/new_nodes/%s_conf.txt" % (vmName))

#Transfer manifest file to the corresponding folder in the puppet server
def executeManifest(vmName):
    api.ftpUpload("./puppet/new_nodes/%s_manifest.txt" % (vmName), "/etc/puppetlabs/code/environments/production/manifests/hosts/%s.pp" % (vmName))
    api.removeLocalFile("./puppet/new_nodes/%s_manifest.txt" % (vmName))
    api.removeLocalFile("./puppet/new_nodes/%s_preManifest.txt" % (vmName))

#Retrieve the manifest file from puppet server so that onetouch server is able reconfigure the manifest file via web
def retrieveManifest(vmName):
    api.ftpDownload("/etc/puppetlabs/code/environments/production/manifests/hosts/%s.pp" % (vmName), "./puppet/reconf_nodes/%s_manifest.txt" % (vmName))

#It will always push the latest manifest file to the puppet server when technician click on update
def updateManifest(vmName):
    api.ftpUpload("./puppet/reconf_nodes/%s_manifest.txt" % (vmName), "/etc/puppetlabs/code/environments/production/manifests/hosts/%s.pp" % (vmName))
    api.removeLocalFile("./puppet/reconf_nodes/%s_manifest.txt" % (vmName))
    #api.sshCommand("/puppet/scripts/restart_vm.sh %s &" % (vmName)) #Restart remote VM
    api.rebootVirtualMachine(vmName) #Restart remote VM

#Completely remove the virtual machine from vcenter
#Remove signed certificate from the puppet server
#Remove related manifest file from the puppet server
def destroyMachine(vmName, certName):
    api.sshCommand("puppet resource vsphere_vm /Datacenter/vm/%s ensure=stopped" % (vmName))
    api.sshCommand("puppet node purge %s" % (certName))
    api.sshCommand("puppet resource vsphere_vm /Datacenter/vm/%s ensure=absent" % (vmName))
    api.removeRemoteFile("/etc/puppetlabs/code/environments/production/manifests/hosts/%s.pp" % (vmName))


#NOTE: This part is important
#When puppet agent is installed on the virtual machine, it will send it certificate to the puppet server for authentication
#It will also, send a web request to OneTouch server to sign the certificate.
def signCert(fqdn):
    #Since there will be a delay,
    #This is to ensure that certificate is available.
    for i in range(30): #Retry up to 30 times at the cycle of 5 seconds
        try:
            certName = api.sshCommandDisplay("/opt/puppetlabs/bin/puppetserver ca list | grep -owi %s" % (fqdn))[0].replace("\n","") #Check weather certificate exist in the puppet server base on fqdn
        except IndexError:
            certName = None
        if fqdn == certName:
            break
        time.sleep(5)

    if fqdn == certName:
        api.sshCommand("/opt/puppetlabs/bin/puppetserver ca sign --certname %s" % (fqdn)) #Signing the certificate
        return True
    else:
        return False

