import sublime, sublime_plugin
import subprocess,sys
import re, json, os
import time

def getConfig(opt):
    ''' loads the config stuff'''
    plugin_path = '%s/SubTunnel' % (sublime.packages_path())
    config = '%s/config.json' % plugin_path
    
    if os.path.exists(config)==True:
        f=open(config).read()
        options = json.loads(f)

    return options[opt]


def getHoudiniPorts():
    ''' 
        Extracts lowest port of currently running houdini processes.
        
        Make susre to run "openport -a" hscript command from Houdini before 
        Otherwise connection will not be possible
        Houdini starts up with two open ports but none of them are available to hcommand tool

        TODO - Instead of picking up the lowest port we can test all the ports for connection. 
        The one where connectino goes through (there will be only one if openport -a is run)
        is the correct port 

    '''
    cmd = "lsof -n -i4"  # -n list things faster
    print (cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_stdout, cmd_stderr = p.communicate()  

    pids = {}
    lines = cmd_stdout.decode('ascii').strip().split('\n')
    for line in lines:
        line = [x.strip() for x in line.split(' ') if x !=''] # remove whitespaces
        # print (line)
        bin = line[0]
        pid = line[1]
        port = line[8]

        # keep only houdini processes
        if bin.find('houdini')!=-1 or bin.find('hescape')!=-1:

            if port.startswith("*"): # remove local addresses - TODO - platofrm specific UNIX
                print (bin, pid, port)

                port = int(port[2:]) # keep only digits, remove *: - TODO - platform dependant 
                pid = int(pid)
                # keep lower one
                if pid in pids.keys():
                    if pids[pid] > port:  # if found lower port  - keep it
                        pids[pid] = port
                else:
                    pids[pid] = port      # if pid is not there just use it

    print (pids) # gets lowest open ports of houdini sessions
    return pids

def getHipName( port):

    hcommand = '%s' % getConfig('hcommand')

    cmd = '''%s %s echo \\`\\$HIPNAME''' % (hcommand, port)
    print (cmd)

    cmd_stdout = ""
    cmd_stderr = ""
    hipname = "NO CONNECTION"

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)             # wait one second
    if p.poll() == None:
        p.terminate()
    else:
        cmd_stdout, cmd_stderr = p.communicate()  


    if cmd_stdout=='':
        print ("No Connection on port: %s" % port)
    else:
        hipname = cmd_stdout.decode('ascii').strip()
                  
    return hipname


def savePort( choice, pidsDict):

    if choice!=-1:
        plugin_path = '%s/SubTunnel' % (sublime.packages_path())
        config = '%s/config.json' % plugin_path


        pid = list(pidsDict.keys())[choice]
        # pid = str(pid)           # convert to string representation - sometimes there was a problem to correcly conver to integrals
                                 # we will stick with strings for now - which is a bit inconsistent, pids -> strings, ports->ints

        port = pidsDict[pid]['port']

        
        if os.path.exists(config)==True:
            f=open(config).read()
            options = json.loads(f)

        else:
            options = {}

        options['port']=port
        options['hipfile']=pidsDict[pid]['hipfile']
        

        f = open(config, 'w')
        f.write(json.dumps(options))
        pass

def buildPortList(pidsDict):
    ''' Build Sublime Menu with list of open ports '''

    portName_list = []
    port_list = []
    for pid, ports in pidsDict.items():


        _str = ''
        for name, value in ports.items():
            print ("   ",name, value)
            if name == 'hipfile':
                _str = _str+'%20s\t' % (value)
            elif name == 'port':
                _str = _str+'%s: %s\t' % (name, value)
                port_list.append(value)
            else:
                _str = _str+'%s: %s\t' % (name, value)

        _str = _str+'pid: %s' % pid

        portName_list.append(_str)

    for i in portName_list:
        print (i)
    # for i in port_list:
    #     print (i)
    return portName_list

