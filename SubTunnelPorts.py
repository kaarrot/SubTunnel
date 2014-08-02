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
        Extract lowest port of currently running houdini processes - this ma not always be true.
        TODO - test all the ports for connection. One of the ports (usaually above 30000)
        will not be accessible
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
    ''' Build a menu options list '''

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


# def getRunnigProcesses(self):
#     cmd = "top -b -n 1 | grep -i -e hescape-bin -e hmaster-bin -e houdini -e hescape"

#     p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
#     cmd_stdout, cmd_stderr = p.communicate()   

#     print (cmd_stdout)
#     lines = cmd_stdout.decode('ascii').strip().split('\n')

#     pids = []
#     for line in lines:   
#         line = line.strip()           # remove leading whitesaces, or split command may sometimes fail
#                                       # depending on the pid id and the order they appear
#         pid = line.split(' ')[0]
#         pids.append(pid)


#     # # convert strings to ints
#     pidsInt = []
#     if len(pids)>0 and pids[0]!='':
#         for i in pids:
#             try:
#                 pidsInt.append(int(i))
#             except:
#                 print("Pid is not integral value:", sys.exc_info()[0], i)
#                 pass
#     else:
#         print ("...No Pids")    
    
#     # return pids
#     return pidsInt

# def getLastOpenPort(self, pid):
#     cmd = "lsof -a -p%s -i4" % pid
#     print (cmd)
#     p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
#     cmd_stdout, cmd_stderr = p.communicate()   

#     ports = cmd_stdout.decode('ascii').strip().split('\n')
#     for port in ports:
#         print (port)

    
#     # get the last open port where the '*:' !!! this may not be portable !!!
#     # Houdini starts up with a few open port but non of them are open to hcommand tool

#     # Option 2  - TODO need to add timeout in case the port from houdini has not been opened
#     # (Above may not be needed if below works len(ports_list)<=1 )
#     # In this case hcommand is retrying and the subprocess waits indefinitely
#     # As a temporary solution (This is optimal for now) we can narrow down the search port <30000
#     # TODO on other machines what is the safe port threshold not to interfere with other open houdini ports             
    
#     openport = None
#     ports_list = []
#     for port in ports:
#         # print (port)
#         if port.find('*:')!=-1:
#             openport = int(port.split('*:')[1].split(' ')[0])
#             ports_list.append(openport)

#     # make sure the openport -a command has been call beforehand
#     # otherwise the only open ports on houdini's end are:
#     #  TCP *:52453 (LISTEN)               ----> No Response
#     #  TCP localhost:14726 (LISTEN)       ----> ignored by SubTunnel

#     # The proper list of ports should look as follow,
#     # TCP *:52453 (LISTEN)
#     # TCP *:28258 (LISTEN)
#     # TCP localhost:14726 (LISTEN)

#     # Note that with openport -a houdini reuses already open port
#     # and doesn't start a new one

#     ports_list = sorted(ports_list)
#     if len(ports_list)<=1:
#         openport = None
#     else:
#         openport = ports_list[0]         # sort and pick up the lowest number


#     print (openport)

#     if openport == None:
#         print ("Houdini session %s has no openport" % pid)
#     else:
#         print ("found open %s " % openport)

#     return openport