#Everything to do with collection or inserting data to database will be done through here
#All query are parameterized
#NOTE: 
#User role: 1 - User, 2 - Management, 3 - Technician, 0 - Admin
#Request status: 1 - Pending, 2 - Approved, 3 - Provisioned, 4 - Certificate, 5 - Completed , 6 - Expiring, 7 - Destroyed, 0 - Rejected
#Change Request status: 0 - Incomplete, 1 - Completed, 99 - Extend expiry request
#Author: Nigel Chen Chin Hao

import MySQLdb
from datetime import datetime, timedelta
import gc
import api

class Database:

    #Initialized Connection to database
    def __init__(self):
        print("Connecting to mySQL server ...")
        self.conn = MySQLdb.connect(
        host = "127.0.0.1",
        user = "onetouch",
        passwd = "P@ssw0rd",
        db = "puppet_db"
        )
        self.cur = self.conn.cursor()
        print("Connected to mySQL server")

    # 1 - User, 2 - Management, 3 - Technician, 0 - Admin
    def createUser(self, name=None, email=None, password=None):
        if name != None and email != None and password != None:
            self.cur.execute('INSERT INTO User (Name, Email, Password, Role) VALUES (%(name)s, %(email)s, %(password)s, 1);', {
                'name': name,
                'email': email,
                'password': api.hashValue(password+email)
                })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False

    #Authenticate user with email and password
    #Return the role of user accordingly
    def loginUser(self, email, password):
        data = None
        if email != None and password != None:
            self.cur.execute('SELECT ID, Password FROM User WHERE Email=%(email)s', 
                {
                    'email': email
                })
            preCheck = self.cur.fetchall()
            if len(preCheck) == 1:
                if api.hashValue(password+email) == preCheck[0][1]:
                    self.cur.execute('SELECT ID, Name, Role FROM User WHERE ID = %(preCheck)s',
                        {
                            'preCheck': preCheck[0][0]
                        })
                    data = self.cur.fetchall()[0]
                    check = True
                else:
                    check = False
            else:
                check = False
        else:
            check = False
        gc.collect()
        return check, data
    #TODO: Check for any identical vm name & hostname to prevent clash 
    #Request virtual machine to create upon approval
    def requestMachine(self, uid=None, vmName=None, cpuCore=None, memorySize=None,storageSize=None, hostname=None, os=None, requirements=None):
        if uid != None and vmName != None and cpuCore != None and memorySize != None and storageSize != None and hostname != None and os != None:
            self.cur.execute('INSERT INTO Machine (VmName, CpuCore, MemorySize, StorageSize, Hostname, OperatingSystem, AdditionalRequirement) VALUES (%(VmName)s, %(CpuCore)s, %(MemorySize)s, %(StorageSize)s, %(Hostname)s, %(OperatingSystem)s, %(AdditionalRequirement)s)', 
                {
                    'VmName': vmName,
                    'CpuCore': cpuCore,
                    'MemorySize': memorySize,
                    'StorageSize': storageSize,
                    'Hostname': hostname,
                    'OperatingSystem': os,
                    'AdditionalRequirement': requirements
                })
            mid = self.cur.execute('SELECT LAST_INSERT_ID() FROM Machine')
            self.cur.execute('INSERT INTO Request (UserID, MachineID, Status) VALUES (%(UserID)s, %(MachineID)s, 1)', {
                    'UserID': uid,
                    'MachineID': mid
                })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False

    #Get basic vm details of the vm requested
    def getMachine(self, rid=None):
        if rid != None:
            self.cur.execute('SELECT VmName, CpuCore, MemorySize, OperatingSystem, Hostname\
            FROM Machine\
            JOIN Request\
            ON Machine.ID = Request.MachineID\
            WHERE Request.ID = %(RequestID)s', {
                'RequestID': rid
            })
            requests = self.cur.fetchall()
            gc.collect()
            return requests[0]
        else:
            return None

    #Update the status of the virtual machine accordingly
    #1 - Pending, 2 - Approved, 3 - Provisioned, 4 - Certificate, 5 - Completed , 6 - Expiring, 7 - Destroyed, 0 - Rejected
    def updateRequestStatus(self, rid=None, status=None):
        if rid != None and status != None:
            self.cur.execute('UPDATE Request SET Status = %(Status)s WHERE ID = %(RequestID)s', 
                {
                    'Status': status,
                    'RequestID': rid
                })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False

    #Extenstion of @updateRequestStatus where it update the status of the machine upon successful deployment
    #Works for windows only
    def updateRequestStatusWin(self, vmName=None, status=None):
        if vmName != None and status != None:
            self.cur.execute('UPDATE Request\
            JOIN Machine\
            ON Machine.ID = Request.MachineID\
            SET Status = %(Status)s\
            WHERE Machine.VmName = %(VmName)s', {
                'Status': status,
                'VmName': vmName
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False
    #Extenstion of @updateRequestStatus where it update the status of the machine upon successful deployment
    #Works for linux only
    def updateRequestStatusDeb(self, hostname=None, status=None):
        if hostname != None and status != None:
            self.cur.execute('UPDATE Request\
            JOIN Machine\
            ON Machine.ID = Request.MachineID\
            SET Status = %(Status)s\
            WHERE Machine.Hostname = %(Hostname)s', 
            {
                'Hostname': hostname,
                'Status': status
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False

    #TODO: Check for any identical ip address to prevent clash 
    #Update the network address of virtual machine when technician assign
    def updateMachineAddress(self, mn=None):
        if mn != None:
            self.cur.execute('UPDATE Machine\
            JOIN Request\
            ON Machine.ID = Request.MachineID\
            SET Address = %(Address)s, Netmask = %(Netmask)s, Gateway = %(Gateway)s, Dns = %(Dns)s\
            WHERE Request.MachineID = %(MachineID)s', {
                'Address': mn.address, 
                'Netmask': mn.netmask,
                'Gateway': mn.gateway,
                'Dns': mn.dns,
                'MachineID': mn.rid
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False

    #List all the pending request waiting for approval
    def listPendingRequest(self):
        self.cur.execute('SELECT Request.ID, User.Name, Machine.VmName, Machine.CpuCore, Machine.MemorySize, Machine.OperatingSystem, Machine.StorageSize\
        FROM Request\
        INNER JOIN User ON Request.UserID = User.ID\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        WHERE Status = 1')
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    #List all the approved virtual machine waiting to be provisioned by the technican
    def listApprovedRequest(self):
        self.cur.execute('SELECT Request.ID, Machine.Hostname, Machine.VmName, Machine.CpuCore, Machine.MemorySize, Machine.OperatingSystem, Machine.StorageSize\
        FROM Request\
        INNER JOIN User ON Request.UserID = User.ID\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        WHERE Status = 2')
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    #List all the provisioned virtual machine waiting to be verified by the technican
    def listProvisionedRequest(self):
        self.cur.execute('SELECT Request.ID, Machine.VmName, Machine.Address, Machine.Hostname, Machine.OperatingSystem\
        FROM Request\
        INNER JOIN User ON Request.UserID = User.ID\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        WHERE Status = 4')
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    #List all the provisioned virtual machine
    def listCompletedRequest(self):
        self.cur.execute('SELECT Request.ID, Machine.VmName, Machine.Address, Machine.Hostname, Machine.OperatingSystem, COUNT(IF(Change_Request.Status=0 OR Change_Request.Status=99, 1,NULL)) AS ChangeReqNo, COUNT(IF(Change_Request.Status=99, 1,NULL)) AS ChangeExpNo\
        FROM Request\
        INNER JOIN User ON Request.UserID = User.ID\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        LEFT OUTER JOIN Change_Request ON Request.ID = Change_Request.RequestID\
        WHERE Request.Status = 5\
        OR Request.Status = 6\
        GROUP BY Request.ID\
        ORDER BY ChangeExpNo DESC, ChangeReqNo DESC, Request.ID')
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    #List the specific details of the vm requested
    def listSpecificProvisionedRequest(self, rid):
        self.cur.execute('SELECT Request.ID, Machine.VmName, Machine.CpuCore, Machine.MemorySize, Machine.StorageSize, Machine.Address, Machine.Netmask, Machine.Gateway, Machine.Dns,  Machine.Hostname, Machine.OperatingSystem, Machine.AdditionalRequirement\
        FROM Request\
        INNER JOIN User ON Request.UserID = User.ID\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        WHERE Request.ID = %(RequestID)s', {
            'RequestID': rid
        })
        requests = self.cur.fetchall()
        gc.collect()
        return requests[0]

    #List the change request of the specific vm if any
    def listSpecificProvisionedChangeRequest(self, rid):
        self.cur.execute('SELECT Change_Request.Date, Change_Request.Information\
        FROM Request\
        INNER JOIN Change_Request ON Change_Request.RequestID = Request.ID\
        WHERE Request.ID = %(RequestID)s AND Change_Request.Status = 0\
        ORDER BY Change_Request.ID DESC', {
            'RequestID': rid
        })
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    #Get the extension of vm request of the specific vm if any
    def listSpecificProvisionedExtensionRequest(self, rid):
        self.cur.execute('SELECT Change_Request.Information, Request.Expiry\
        FROM Request\
        INNER JOIN Change_Request ON Change_Request.RequestID = Request.ID\
        WHERE Request.ID = %(RequestID)s AND Change_Request.Status = 99\
        ORDER BY Change_Request.ID DESC', {
            'RequestID': rid
        })
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    #List all the virtual machine that the current user owned
    def listCurrentVm(self, uid):
        self.cur.execute('SELECT Request.ID, Machine.VmName, Machine.CpuCore, Machine.MemorySize, Machine.OperatingSystem, Machine.StorageSize, Machine.Address, Request.Status, Machine.Hostname, Request.Expiry\
        FROM Request\
        INNER JOIN User ON Request.UserID = User.ID\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        WHERE User.ID = %(UserID)s', {
            'UserID': uid
        })
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    #Submit request of any changes needed to the technician to change
    def changeRequest(self, rid, info):
        self.cur.execute('INSERT INTO Change_Request (RequestID, Date, Information) VALUES (%(RequestID)s, %(Date)s, %(Information)s)', {
            'RequestID': rid,
            'Date': datetime.now().strftime('%Y-%m-%d'),
            'Information': info
        })
        self.conn.commit()
        gc.collect()
        
        return True

    #Submit extension of virtual machine of to the technician to change its expiry
    def extensionRequest(self, rid, info):
        self.cur.execute('INSERT INTO Change_Request (RequestID, Date, Information, Status) VALUES (%(RequestID)s, %(Date)s, %(Information)s, 99)', {
            'RequestID': rid,
            'Date': datetime.now().strftime('%Y-%m-%d'),
            'Information': info
        })
        self.conn.commit()
        gc.collect()
        
        return True

    #Reset status of change request upon completion by technician
    def updateChangeRequest(self, rid=None):
        if rid != None:
            self.cur.execute("UPDATE Change_Request\
            SET Status = 1\
            WHERE RequestID = %(RequestID)s AND Status = 0", {
                'RequestID': rid
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False

    #Reset status of extension request upon completion whether it is approved or rejected
    def updateExtensionRequest(self, rid=None):
        if rid != None:
            self.cur.execute("UPDATE Change_Request\
            SET Status = 1\
            WHERE RequestID = %(RequestID)s AND Status = 99", {
                'RequestID': rid
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False


    #Upon successful completion of vm, automatically send email to the corresponding user
    def emailCompletion(self, rid):
        self.cur.execute('SELECT Machine.VmName, Machine.CpuCore, Machine.MemorySize, Machine.StorageSize, Machine.Address, Machine.Hostname, Machine.OperatingSystem, User.Name, User.Email\
        FROM Request\
        INNER JOIN User ON Request.UserID = User.ID\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        WHERE Request.ID = %(RequestID)s', {
            'RequestID': rid
        })
        requests = self.cur.fetchall()
        gc.collect()
        return requests[0]

    #List all the user and its details for administrative purpose
    def listUser(self):
        self.cur.execute('SELECT User.ID, User.Email, User.Name, User.Role, COUNT(IF(status=5 OR status=6,1, NULL)) AS ApprovedStatus,  COUNT(IF(status=0,1, NULL)) AS RejectedStatus, COUNT(IF(status>0 AND status<5,1, NULL)) AS PendingStatus\
        FROM User\
        LEFT OUTER JOIN Request\
        ON Request.UserID = User.ID\
        GROUP BY User.ID')
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    #Promote or demote user access to the system
    def updateUserRole(self, uid=None, roleId=None):
        if uid != None and roleId != None:
            self.cur.execute("UPDATE User\
            SET Role = %(Role)s\
            WHERE User.ID = %(UserID)s", {
                'Role': roleId,
                'UserID': uid
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False

    #Update puppet certificate to the database for later use
    def updateWinCertName(self, vmName=None, fqdn=None):
        if vmName != None and fqdn != None:
            self.cur.execute("UPDATE Machine\
            SET CertName = %(CertName)s\
            WHERE VmName = %(VmName)s", {
                'CertName': fqdn,
                'VmName': vmName
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False
    
    #Update puppet certificate to the database for later use
    def updateDebCertName(self, fqdn=None):
        if fqdn != None:
            self.cur.execute("UPDATE Machine\
            SET CertName = %(CertName)s\
            WHERE Hostname = %(Hostname)s", {
                'CertName': fqdn,
                'Hostname': fqdn
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False

    #Change the expiry date of the virtual machine
    def updateExpiryRequest(self, rid=None, date=None):
        if rid != None and date != None:
            self.cur.execute("UPDATE Request\
            SET Expiry = %(Expiry)s\
            WHERE ID = %(RequestID)s", {
                'Expiry': date,
                'RequestID': rid
            })
            self.conn.commit()
            gc.collect()
            return True
        else:
            return False
    #Get the expiry date of the virtual machine
    def getExpiryRequest(self, rid=None):
        if rid != None:
            self.cur.execute("SELECT Expiry\
            FROM Request\
            WHERE ID = %(RequestID)s", {
                'RequestID': rid
            })

            requests = self.cur.fetchall()
            gc.collect()
            return requests[0][0]
        else:
            return False

    #List the vm that is going to be expired and email to user
    def listExpiringVm(self):
        self.cur.execute("SELECT Request.ID, Machine.VmName, Machine.Hostname, User.Name, User.Email\
        FROM Request\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        INNER JOIN User ON Request.UserID = User.ID\
        WHERE Request.Status = 5\
        AND Request.Expiry < %(DateNow)s", {
            'DateNow': datetime.now() + timedelta(7),
        })
        requests = self.cur.fetchall()
        gc.collect()
        return requests
    #List the vm that is expired and destory the vm
    def listExpiredVm(self):
        self.cur.execute("SELECT Request.ID, Machine.VmName, Machine.CertName\
        FROM Request\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        WHERE Request.Status = 6\
        AND Request.Expiry <= %(DateNow)s", {
            'DateNow': datetime.now().strftime('%Y-%m-%d'),
        })
        requests = self.cur.fetchall()
        gc.collect()
        return requests

    def getDestroyVm(self, rid=None, uid=None):
        self.cur.execute("SELECT Request.ID, Machine.VmName, Machine.CertName\
        FROM Request\
        INNER JOIN Machine ON Request.MachineID = Machine.ID\
        INNER JOIN User ON Request.UserID = User.ID\
        WHERE Request.ID = %(RequestID)s\
        AND User.ID <= %(UserID)s", {
            'RequestID': rid,
            'UserID': uid,
        })
        requests = self.cur.fetchall()
        gc.collect()
        return requests[0]
