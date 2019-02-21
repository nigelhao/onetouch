#Custom API for different purpose
#Author: Nigel Chen Chin Hao

import smtplib
import paramiko
import os
import hashlib
from email.message import EmailMessage

from pyVmomi import vim
from pyVim.connect import SmartConnect, SmartConnectNoSSL, Disconnect
import getpass
import vmutils

#The usage of paramiko sometime causes a long delay when starting the onetouch application
#Authentication to allow SSH to puppet server
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
k = paramiko.RSAKey.from_private_key_file(os.path.expanduser('/root/.ssh/id_rsa'))

#Initialized Connection to vCenter to perform remote vm action
si = None
try:
    print("Connecting to vCenter ...")
    #To prevent timeout configure:
    #/usr/local/lib/python3.5/dist-packages/pyVmomi/SoapAdapter.py:
    #CONNECTION_POOL_IDLE_TIMEOUT_SEC = -1
    si = SmartConnectNoSSL(host="10.5.27.20", user="administrator@fyp.nyp", pwd="P@ssw0rd", port=443) #Bypass SSL check
    #si = SmartConnect(host="10.5.27.20", user="administrator@fyp.nyp", pwd="P@ssw0rd", port=443) 
except IOError:
    print("Failed to connect to vCenter")
    pass
else:
    print("Connected to vCenter")

#Run command on puppet server without displaying output
def sshCommand(command):
    ssh.connect('puppet.fyp.nyp', username='root', pkey=k)
    ssh.exec_command(command)

#Run command on puppet server and displaying output
def sshCommandDisplay(command):
    ssh.connect('puppet.fyp.nyp', username='root', pkey=k)
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout = stdout.readlines()
    ssh.close()
    return stdout

#Upload to puppet server
def ftpUpload(local, remote):
    ssh.connect('puppet.fyp.nyp', username='root', pkey=k)
    ftp=ssh.open_sftp()
    ftp.put(local, remote)
    ftp.close()
    ssh.close()

#Download from puppet server
def ftpDownload(remote, local):
    ssh.connect('puppet.fyp.nyp', username='root', pkey=k)
    ftp=ssh.open_sftp()
    ftp.get(remote, local)
    ftp.close()
    ssh.close()

def removeLocalFile(file):
    if os.path.exists(file):
        os.remove(file)

#Delete a file in remote puppet server
def removeRemoteFile(file):
    ssh.connect('puppet.fyp.nyp', username='root', pkey=k)
    try:
        ftp=ssh.open_sftp()
        ftp.remove(file)
        ftp.close()
        ssh.close()
    except FileNotFoundError:
        print("File not found") 

#Upon updating manifest file, restart vm to pull latest config to vm
def rebootVirtualMachine(vmName):
    # Finding source VM
    vm = vmutils.get_vm_by_name(si, vmName)

    # Perform safe vm reboot
    try:
        vm.RebootGuest()
    except:
        # forceably shutoff/on
        # need to do if vmware guestadditions isn't running
        vm.ResetVM_Task()

#Hash value to ensure user password security in database
def hashValue(data):
    hashData = hashlib.sha256(data.encode()).hexdigest()
    return hashData

def sendEmail(email, content, managerEmailArr=None):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("onetouch.fyp@gmail.com", "B8xkLVvdwfb")
        msg = EmailMessage()
        msg['Subject'] = 'OneTouch - Virtual Machine'
        msg['From'] = 'onetouch.fyp@gmail.com'
        string_of_emails = email
        if managerEmailArr != None:
            string_of_manager_email = ''
            first = True
            for managerEmail in managerEmailArr:
                if first:
                    string_of_manager_email = managerEmail[0]
                    first = False
                else:
                    string_of_manager_email += ', ' + managerEmail[0]
            msg['Cc'] = string_of_manager_email
        msg['To'] = string_of_emails
        msg.set_content(content)
        server.send_message(msg)
        server.quit()
    except:
        print("Something went wrong")

