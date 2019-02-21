#OneTouch server uses FLASK as the backend framework.
#This main.py is responsible for routing the corresponding path to to correct function
#Within the function, it will run certain logic
#Author: Nigel Chen Chin Hao

from flask import Flask, render_template, flash, request, session, redirect, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, Form, TextField
from wtforms.validators import DataRequired
import datetime
import os
import sys
import time
import database
import api
import threading

sys.path.insert(0,'./puppet')
import puppet_deb
import puppet_win
import puppet_common
import puppet_machine

app = Flask(__name__)
app.secret_key = "VERY SECURE KEY" #For session purposes
db = database.Database()

#This function will run continuouly parallel to the flask server
#Constantly check for any expired or going to expire virtual machine
def checkExpiry():
    print("Thread running in parallel")
    while True:
        #Query datebase to list out virtual machine that is going to expire
        for expiringVm in db.listExpiringVm():
            db.updateRequestStatus(expiringVm[0], 6)
            content = "Dear %s, \n\
            The following virtual machine is expiring soon:\n\
            VM Name: %s \n\
            Hostname: %s \n\n\
            Machine will be terminated by technician when expired.\n\
            Please login to extend your virtual machine as soon as possible.\n\n\
            Best regards,\n\
            One Touch Service" % (expiringVm[3], expiringVm[1], expiringVm[2])
            api.sendEmail(expiringVm[4], content)
            print("Warning sent: " + expiringVm[1])

        #Query data base to list out virutal machine that is expired
        for expiredVm in db.listExpiredVm():
            #Set machine to shutdown status. Waiting for technician to terminate
            puppet_common.shutdownMachine(expiredVm[1])
            db.updateRequestStatus(expiredVm[0], 7)
            content = "Dear %s, \n\
            The following virtual machine is expired:\n\
            VM Name: %s \n\n\
            Please contact your technician before it is fully terminated.\n\n\
            Best regards,\n\
            One Touch Service" % (expiredVm[3], expiredVm[1])
            api.sendEmail(expiredVm[4], content, db.getManagerEmail())
            print("VM Expired: " + expiredVm[1])

        time.sleep(3) #3 second refresh rate
        #time.sleep(3*60*60) #3 hour refresh rate

#Display error page accordingly
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def page_not_found(e):
    return render_template('405.html'), 405

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

@app.route("/")
def index():
    return redirect('/Login')

#Login User and create session for that user
@app.route("/Login")
def login():
    if session.get('login') == True:
        return redirect('/Home')
    else:
        return render_template("Login.html")

@app.route("/LoginForm", methods=['POST'])
def loginForm():
    if request.method == 'POST':
        check, data = db.loginUser(request.form['email'], request.form['password'])
        if check:
            session['uid'] = data[0]
            session['name'] = data[1]
            session['role'] = data[2]
            session['login'] = True
            return "1" #Normal User
        else:
            return "0"
    else:
        return "0"

@app.route("/Logout")
def logout():
    session.clear()
    return redirect("/Login")

@app.route("/Registration")
def registration():
    if session.get('login') == True:
        return redirect('/Home')
    else:
        return render_template("Registration.html")

@app.route("/RegistrationForm", methods=['POST'])
def registrationForm():
    if request.method == 'POST':
        check = db.createUser(request.form['name'], request.form['email'], request.form['password'])
        return "1" #Normal User

#This redirect to the appropriate home page when logged in
@app.route("/Home")
def Home():
    if session.get('login') == True:
        if session['role'] == 1:
            return redirect('/CurrentVm')
        elif session['role'] == 2: 
            return redirect('/VmApproval')
        elif session['role'] == 3:
            return redirect('/VmProvision')
        elif session['role'] == 0:
            return redirect('/CurrentVm')
        else:
            session.clear()
            return redirect('/Login')
    else:
        return redirect('/Login')

#User reuqest virtual machine and wait for approval
@app.route("/VmRequest")
def vmRequest():
    if session.get('login') == True:
        return render_template("VmRequest.html", user=session['role'])
    else:
        return redirect('/Login') 

@app.route("/VmRequestForm", methods=['POST'])
def vmRequestForm():
    vmName = request.form['vmName']
    hostname = request.form['hostname']
    domain = request.form['domain']
    cpu = request.form['cpu']
    memory = request.form['memory']
    storage = request.form['storage']
    osType = request.form['osType']
    requirement = request.form['requirement']

    fqdn = hostname
    if len(domain) != 0:
        fqdn = hostname + "." + domain

    db.requestMachine(session['uid'], vmName, cpu, memory, storage, fqdn, osType, requirement)

    return render_template("VmRequestComplete.html", user=session['role'])

#Higher ups approved request of virtual machine
@app.route("/VmApproval")
def vmApproval():
    if session.get('login') == True:
        if session['role'] == 2 or session['role'] == 0:
            requests = db.listPendingRequest()
            return render_template("VmApproval.html", listArr=requests, user=session['role'])
        else:
            return render_template('404.html'), 404
    else:
        return redirect('/Login') 
    
@app.route("/VmApprovalForm", methods=['POST'])
def vmApprovalForm():
    check = db.updateRequestStatus(request.form['rid'], request.form['action'])
    return redirect('/VmApproval')

#Technician provision virtual machine request
@app.route("/VmProvision")
def vmProvision():
    if session.get('login') == True:
        requests = db.listApprovedRequest()
        return render_template("VmProvision.html", listArr=requests, user=session['role'])
    else:
        return redirect('/Login') 


@app.route("/VmProvisionForm", methods=['POST'])
def vmProvisionForm():
    rid = request.form['rid']
    address = request.form['address']
    netmask = request.form['netmask']
    gateway = request.form['gateway']
    dns= request.form['dns']

    mn = puppet_machine.Machine_Networking(rid, address, netmask, gateway, dns)
    check = db.updateMachineAddress(mn)

    data = db.getMachine(rid)
    m = puppet_machine.Machine(data[0], str(data[1]), str(data[2]), data[3], address, netmask, gateway, dns, data[4])
    check = vmCreation(m)

    check = db.updateRequestStatus(rid, 3)
    return redirect('/VmProvision')

@app.route("/VmCompletion")
def vmCompletion():
    if session.get('login') == True:
        requests = db.listProvisionedRequest()
        return render_template("VmCompletion.html", listArr=requests, user=session['role'])
    else:
        return redirect('/Login') 

@app.route("/GetMachineData", methods=['POST'])
def getMachineData():
    rid = request.form['rid']
    data = db.listSpecificProvisionedRequest(rid)
    data2 = db.listSpecificProvisionedChangeRequest(rid)
    data3 = db.listSpecificProvisionedExtensionRequest(rid)
    try:
        extension = data3[0][0].split(" ")[0]
        expiry = str(data3[0][1])
    except:
        extension = "None"
        expiry = "None"
    puppet_common.retrieveManifest(data[1])
    filePath = "./puppet/reconf_nodes/%s_manifest.txt" % data[1]
    arrLines = open(filePath, "r").readlines()
    lines = ""
    for line in arrLines:
        lines += line

    return jsonify({
        'rid' : data[0],
        'vmName': data[1],
        'cpu' : data[2],
        'memory' : data[3],
        'storage' : data[4],
        'address' : data[5],
        'netmask' : data[6],
        'gateway' : data[7],
        'dns' : data[8],
        'hostname' : data[9],
        'os' : data[10],
        'req' : data[11],
        'man' : lines,
        'change': data2,
        'extension': extension,
        'expiry': expiry
    })

@app.route("/GetPreMachineData", methods=['POST'])
def getPreMachineData():
    rid = request.form['rid']
    data = db.listSpecificProvisionedRequest(rid)

    return jsonify({
        'vmName': data[1],
        'cpu' : data[2],
        'memory' : data[3],
        'storage' : data[4],
        'hostname' : data[9],
        'os' : data[10],
        'req' : data[11]
    })

@app.route("/VmCompletionForm", methods=['POST'])
def vmCompletionForm():
    check = db.updateRequestStatus(request.form['rid'], request.form['action'])
    if check:
        filePath = "./puppet/reconf_nodes/%s_manifest.txt" % request.form["vmName"]
        f = open(filePath, "w")
        f.write(request.form["manifest"])
        f.close()
        puppet_common.updateManifest(request.form["vmName"])

        #By default 6 month lifespan VM (6 Months)
        date = datetime.datetime.now() + datetime.timedelta(6*365/12) 
        db.updateExpiryRequest(request.form['rid'], date)

        #SEND EMAIL
        data = db.emailCompletion(request.form['rid'])
        content = "Dear %s, \n\
        We are glad to inform you that your requested virtual machine \"%s\" has been deployed. \n\
        VM Name: %s \n\
        CPU: %s Core\n\
        RAM: %s MB\n\
        Storage: %s GB\n\
        Operating System: %s \n\
        Hostname: %s \n\n\
        You can connect to the machine with the following IP address: %s \n\n\
        Best regards,\n\
        One Touch Service" % (data[7], data[0], data[0], data[1], data[2], data[3], data[6], data[5], data[4])
        api.sendEmail(data[8], content, db.getManagerEmail())

    return redirect('/VmCompletion')

def vmCreation(m):
        if m.osType == "WinServer_2016":
            puppet_win.configuration(m)
            puppet_win.preManifest(m)
        elif m.osType == "Debian_9.3":
            puppet_deb.configuration(m)
            puppet_deb.manifest(m)

        return True

@app.route("/VmReconfigure")
def vmReconfigure():
    if session.get('login') == True:
        requests = db.listCompletedRequest()
        return render_template("VmReconfigure.html", listArr=requests, user=session['role'])
    else:
        return redirect('/Login') 

@app.route("/VmReconfigureForm", methods=['POST'])
def vmReconfigureForm():
    filePath = "./puppet/reconf_nodes/%s_manifest.txt" % request.form["vmName"]
    f = open(filePath, "w")
    f.write(request.form["manifest"])
    f.close()
    db.updateChangeRequest(request.form['rid'])
    puppet_common.updateManifest(request.form["vmName"])

    return redirect('/VmReconfigure')

@app.route("/VmExtensionForm", methods=['POST'])
def vmExtensionForm():
    if request.form['action'] != "0":
        date = datetime.datetime.strptime(request.form['date'], "%Y-%m-%d") + datetime.timedelta(int(request.form['action'])*365/12)
        db.updateExpiryRequest(request.form['rid'], date)
        db.updateExtensionRequest(request.form['rid'])
        db.updateRequestStatus(request.form['rid'], 5)
        message = "approved"
    else:
        db.updateExtensionRequest(request.form['rid'])
        message = "rejected"

    data = db.emailCompletion(request.form['rid'])
    content = "Dear %s, \n\
    Your request to extend \"%s\" virtual machine has been %s. \n\n\
    Best regards,\n\
    One Touch Service" % (data[7], data[0], message)
    api.sendEmail(data[8], content)

    return redirect('/VmReconfigure')

@app.route("/CurrentVm")
def currentVm():
    if session.get('login') == True:
        data = db.listCurrentVm(session['uid'])
        dataArr = []
        for d in data:
            d = list(d)
            try:
                d[9] = (d[9] - datetime.date.today()).days
            except:
                d[9] = ""
            dataArr.append(d)
        return render_template("VmCurrent.html", listArr = dataArr, user=session['role'])
    else:
        return redirect('/Login') 

@app.route("/ChangeRequirementForm", methods=['POST'])
def changeRequirementForm():
    if session.get('login') == True:
        check = db.changeRequest(request.form['rid'], request.form['request'])
        return redirect('/CurrentVm')
    else:
        return redirect('/Login')

@app.route("/ChangeExpiryForm", methods=['POST'])
def changeExpiryForm():
    if session.get('login') == True:
        check = db.extensionRequest(request.form['rid'], request.form['request'])
        return redirect('/CurrentVm')
    else:
        return redirect('/Login')

@app.route("/ForceRestartVmForm", methods=['POST'])
def forceRestartVmForm():
    if session.get('login') == True:
        puppet_common.forceRestartMachine(request.form['action'])
        return redirect('/CurrentVm')
    else:
        return redirect('/Login')


@app.route("/RequestDestroyVmForm", methods=['POST'])
def requestDestroyVmForm():
    if session.get('login') == True:
        data = db.getDestroyVm(request.form['rid'])
        puppet_common.shutdownMachine(data[1])
        db.updateRequestStatus(data[0], 7)
        return redirect('/CurrentVm')
    else:
        return redirect('/Login')

@app.route("/DestroyVmForm", methods=['POST'])
def destroyVmForm():
    if session.get('login') == True:
        data = db.getDestroyVm(request.form['rid'])
        puppet_common.destroyMachine(data[1],data[2])
        db.updateRequestStatus(data[0], 8)
        content = "Dear %s, \n\
        The following virtual machine has been successfully terminated:\n\
        VM Name: %s \n\n\
        Virtual machine and all its content is destroyed.\n\n\
        Best regards,\n\
        One Touch Service" % (data[3], data[1])
        api.sendEmail(data[4], content, db.getManagerEmail())
        print("VM Destroyed: " + data[1])
        return redirect('/VmReconfigure')
    else:
        return redirect('/Login')

#For signing of puppet certificate
@app.route("/SignCert", methods=['POST'])
def signCert():
    hostname = request.form['hostname']
    osType = request.form['type']
    fqdn = (hostname + ".fyp.nyp").lower()

    if osType == 'Linux':
        result = puppet_common.signCert(fqdn)
        if result:
            db.updateDebCertName(fqdn)
            db.updateRequestStatusDeb(fqdn,4)
    elif osType == 'Windows':
        result = puppet_common.signCert(fqdn)
        unformatUUID = request.form['uuid']
        formatUUID = puppet_win.formatUUID(unformatUUID)
        vmName = puppet_win.grabVmName(formatUUID)
        puppet_win.postManifest(vmName, fqdn)
        if result:
            db.updateWinCertName(vmName, fqdn)
            db.updateRequestStatusWin(vmName,4)
    if result:
        return "Cert Signed"
    else:
        return "Cert Sign failed"

@app.route("/UserManagement")
def userManagement():
    data = db.listUser()
    return render_template("UserManagement.html", listArr = data, user=session['role'])

@app.route("/UserManagementForm", methods=["POST"])
def userManagementForm():
    cData = request.form['changeData'].split('.')
    db.updateUserRole(cData[0],cData[1])
    return "UPDATED"

#PURPOSE OF TESTING FUNCTION ONLY
@app.route("/test", methods=['GET', 'POST'])
def test():
    #vmNameCheck, hostnameCheck = db.checkRequestMachine("win1_vm", "young_vm.fyp.nyp")
    #addressCheck = db.checkMachineAddress("10.5.27.149")
    #print(vmNameCheck)
    #print(hostnameCheck)
    #print(addressCheck)
    return render_template("test.html")

@app.route("/testForm", methods=['GET', 'POST'])
def testForm():
    data = request.form['vmName']
    db.forceExpiryRequest(data)
    return "Expiry date changed"

if __name__ == "__main__":
    threading.Thread(target = checkExpiry).start()
    app.run(host='0.0.0.0')

