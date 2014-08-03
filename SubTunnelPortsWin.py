import os
import subprocess
import concurrent.futures
import time

'''
    On windows netstat -ab run as subprocess thoufh python does not identify process name
    Instead returns [System]
    In order to circumvent that we need to call TASKLIST first find the pid associated
    with a houdini process and then filter out netstat. This is similar to original
    workflow on linux where we were calling "top" first

'''


def getPidsWin():
    ''' Find pid numbers of running houdini processes''' 

    cmd = ''' TASKLIST '''

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_stdout, cmd_stderr = p.communicate()

    selection = None
    selection = cmd_stdout.decode('ascii').strip()

    # print (cmd_stdout)

    selection = selection.split('\n')
    houdiniLines = []
    for line in selection:
        if line.find('houdini')!=-1 or line.find('hescape')!=-1 or line.find('hmaster')!=-1 :
            line = [x.strip() for x in line.split(' ') if x !='']  # remove separator whitespaces
            houdiniLines.append(' '.join(line))

    pids = {}
    for x in houdiniLines:
        name = x.split(' ')[0]
        pid = x.split(' ')[1]
        pids[pid]=name

    return pids

def getPortsWin(pids):
    ''' Having pid numbers find all the open ports of each houdini process '''

    cmd = ''' netstat -ab'''

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_stdout, cmd_stderr = p.communicate()

    selection = None
    selection = cmd_stdout.decode('ascii').strip()

    selection  = ' '.join([x.strip() for x in selection.split(' ') if x!=''])  # remove separator whitespaces
    selection = selection.split('TCP')  # the line we are interested in start with TCP

    #                       Port                                           PID
    # TCP    complete_name:10845    complete_name:0        LISTENING       844
    for pid in pids.keys():
        ports = []
        for line in selection:
            if line.find(pid)!=-1:
                # print (line)
                line = line.strip()
                port = line.split(' ')[0]
                port = int(port.split(':')[-1])
                # print (port)
                ports.append(port)

        # print (ports)
        ports = sorted(list(set(ports)))  # remove duplicates and sort

        pids[pid]=ports

    return pids

def getHipNameWin( port):

    hcommand = r'''"C:\Program Files\Side Effects Software\Houdini 9.0.858\bin\hcommand"'''


    cmd = '''%s %s echo `$HIPNAME''' % (hcommand, port)
    # print (cmd)

    cmd_stdout = ""
    cmd_stderr = ""
    hipname = "NO CONNECTION"

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2) # when calling with concurent.futures the timeout should be larger then 1 second
    if p.poll() == None:
        p.terminate()
    else:
        cmd_stdout, cmd_stderr = p.communicate()


    if cmd_stdout=='':
        # print ("No Connection on port: %s" % port)
        pass
    else:
        hipname = cmd_stdout.decode('ascii').strip()
                  
    return hipname



pids = getPidsWin()
print (pids)
pids = getPortsWin(pids)
print (pids)


pidsPortOpen = {} # collect just first available
for pid,ports in pids.items():
    connections = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future = executor.map(getHipNameWin, ports)
        connections = (list(future))
    
    print (pid, connections)


    for c in enumerate(connections):
        i = c[0]
        fileName = c[1]
        if fileName != 'NO CONNECTION' and  fileName !='':  
            # print ("+++", c, fileName != 'NO CONNECTION')  # find the first open port
            break
            
    print ("--- port ", ports[i])
    pidsPortOpen[pid] = ports[i]


print (pidsPortOpen)