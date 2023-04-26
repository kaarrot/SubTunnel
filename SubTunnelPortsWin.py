import os
import subprocess
import concurrent.futures
import time
import re

from .SubTunnelPorts import getConfig

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


def subprocess_stream(cmd, cwd=None, str_to_match=None):
    """Executes command as a subprocess and immediately prints the output to stdout."""

    if cwd:
        process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    houdini_open_ports = []
    timeout = 2
    start_t = time.time()
    while True:
        output = process.stdout.readline()
        # print (output)  # DEBUG
        if output == b'' and process.poll() is not None:
            break
      
        output_str = output.decode("ascii").strip()
        # Store lines which contain hodini/hescape.exe PID
        if str_to_match and output_str.find(str_to_match) != -1:
            houdini_open_ports.append(output_str)
        elif ( time.time() - start_t > timeout):
            print ("Interrupt", cmd)
            # Running netstat -a -o block, we need to interrupt as soom as we find the match
            process.terminate()
            # return matching lines
            for i in houdini_open_ports:
                print(i)
            return houdini_open_ports

    err = process.communicate()
    if err:
        print(err)

    return houdini_open_ports

def getPortsWin(pids):
    ''' Having pid numbers find all the open ports of each houdini process '''

    cmd = ''' netstat -a -o'''

    print("Houdini PIDs", pids)

    for pid in pids.keys():
        # print ("Process pid:", pid)
        selection = subprocess_stream(cmd, None, pid)
        # print("Found process with port:", selection)
        #                       Port                                           PID
        # TCP    0.0.0.0:10845    complete_name:0        LISTENING       844
        ports = []
        for line in selection:
            found = re.search('(0.0.0.0):[0-9]+', line)
            if not found:
                continue

            port = found.group()    
            port = int(port.split(':')[-1]) # extract port number
            ports.append(port)

        pids[pid] = list(set(ports)) # remove dups
    
    print ("Found pid {0}, ports:".format(pid, ports))

    return pids

def getHipNameWin(port):

    hcommand = '%s' % getConfig('hcommand')

    cmd = '''%s %s echo `$HIPNAME`''' % (hcommand, port)
    print ("CMD", cmd)

    cmd_stdout = ""
    cmd_stderr = ""
    hipname = "NO CONNECTION"

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1) # when calling with concurent.futures the timeout should be larger then 1 second
    if p.poll() == None:
        print ("terminate", port)
        p.terminate() # Does not work with shell=True in Popen
        return None

    cmd_stdout, cmd_stderr = p.communicate()
    if cmd_stderr != b'':
        print(cmd_stderr)

    if cmd_stdout=='':
        # print ("No Connection on port: %s" % port)
        pass
    else:
        hipname = cmd_stdout.decode('ascii').strip()
    return hipname


##################################

def getHPorts():
    ''' returns the dictionary of process IDs of 
        opened ports and associated scene file names of houdini process
        This is slower but the ideal way since since each open connection 
        on houdini's end is test - and blocked ports are removed from the list 
    '''

    pids = getPidsWin()
    print (pids)
    pids = getPortsWin(pids)
    print (pids)

    # At this point we have Dictionary of pids, where each key have a list of open ports.
    # By elimination - we will probe each port and send a requesst to read Hipfile path.
    # If the reponse does not come back we assume the port is not active.
    pidsPortOpen = {} # collect just first available
    for pid, ports in pids.items():
        hipname = None
        open_port = -1 
        for port in ports:
            hipname = getHipNameWin(port)
            if not hipname:
                continue
            else:
                open_port = port

        if not hipname:
            print("No open port found for pid", pid)
        # print ("connections", pid, connections)

        t = {'port': open_port,'hipfile':hipname}
        pidsPortOpen[pid] = t

    #print ("open Houdini ports: ", pidsPortOpen)
    return pidsPortOpen
