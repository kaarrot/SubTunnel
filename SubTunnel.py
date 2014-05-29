"""
SubTunnel
Kuba Roth: 140427
Info:
A Sublime plugin to send code snippets into running Houdini session
supported nodes:
    SOP - vex: attribwrangle, pointwrangle, volumewrangle, popwrangle, VOPSOP (inline)
          python: 'python' node (new in H13)
    OTLS: code/script tabs in any context (SOP,OBJ,ROP ...) 
"""

import sublime, sublime_plugin
import subprocess,sys
import re, json, os


class Tunnel():
    def __init__(self,window,port):
        self.window = window
        self.port = port
        self.hcommand = '%s %s' % (self.getConfig('hcommand'), self.port)
        self.hipfile = '%s' % (self.getConfig('hipfile'))                   # path to current $HIP

        self.nodeType = self.getNodeType()
        self.nodePath = self.getNodePath()
        self.filePath = self.getFilePath()                                  # path to the temporary code file
        self.codeAsText = self.getCodeAsText()

        #print ("path: ",self.nodePath, "\ntype: ", self.selection, "\n\n")



    def getConfig(self, opt):
        ''' loads the config stuff'''
        plugin_path = '%s/SubTunnel' % (sublime.packages_path())
        config = '%s/config.json' % plugin_path
        
        if os.path.exists(config)==True:
            f=open(config).read()
            options = json.loads(f)

        return options[opt]

    def getNodeType(self):
        # get the selected node type
        # Note a special treatment of backticks (bash specifics)
        cmd = ''' %s "optype -t opfind -N \"/\"\`opselectrecurse(\\"/\\",0)\`" ''' % self.hcommand
        #print ("hscript cmd:", cmd)

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()           
        
        selection = None
        selection = cmd_stdout.decode('ascii').strip()

        if selection == '':
            print ("=== nothing selected ===")
        print (selection)

        return selection

    def getNodePath(self):
        # get the node path
        cmd = ''' %s "opfind -N \"/\"\`opselectrecurse(\\"/\\",0)\`" ''' % self.hcommand      # no space between \"/\"\`o
        #print (cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()           
        
        return cmd_stdout.decode('ascii').strip()

    def getFilePath(self):
        view = self.window.active_view()
        return view.file_name()            # None if the file is not save

   def escape(self, s):

        #char = '$'
        #pos =  s.find(char)           # replace by a regex
        # found = re.search('[$@]+', s)   # search for the following and stop at first occurence

        # print (s)
        print (found.group(0))

        # s = re.sub(r'\$', r'Q', s)
        s = s.replace('$','\$\\')
        s = s.replace('@','\@\\')
        # print ("after",s)

        return s

        # if found==None:
        #     pos = -1
        # else:
        #     pos = found.start()

        # if pos != -1:
        #     front = s[:pos]
        #     back = s[pos:]  
        #     # interleave everything with '\'
        #     back = ['\%s'% c for c in back]
        #     back = ''.join(back)
        #     print(front+back)
        #     return front+back    
        # else:
        #     return s
    
        # test: print escape("vector x = $P + 12+$e +@e - 11;", "@") 

    def getCodeAsText(self):
        view = self.window.active_view()
        codeText = view.substr(sublime.Region(0, view.size()))

        # Treat \n in the strings diferently then new lines at the end of the line
        temp = []
        textSplited = re.split('((?s)".*?")', codeText)
        for x in textSplited:
            y = x.replace(r"\n", r"\\\\n")         # escape new line inside the quotes
            y = self.escape(y)

            # print (x, y)

            temp.append(y)
        codeText = ''.join(temp)


        codeText = codeText.replace("\n", "\\n")         # escape new line at the end of the line
        codeText = codeText.replace("\"", "\\\\\\\"")    # crazy - double escaping


        '''
            this command works from the bash
            hcommand 2223 "opparm /obj/geo1/python1 python \"print \\"______cccB\\"  \"  "
                          ^                                 ^       ^            ^            
                          queue           single escape quote       |            |
                                                                    double  escape
        '''

        return codeText


class SubTunnelCommand(sublime_plugin.WindowCommand):
    
    ''' hdaRun is a sub-function to be able to access previously defined Tunnel()
        the callback script in show_quick_panel implicitly expects only one arguments - choice index
        Also I wasn't able to initialize the SubTunnelCommand class and define the Tunnel() in constructor
        Probably because the SubTunnelCommand is a special type of class and Sublime does some stuff under the hood
    '''

    def getPort(self):
        plugin_path = '%s/SubTunnel' % (sublime.packages_path())
        config = '%s/config.json' % plugin_path
        

        f=open(config).read()
        options = json.loads(f)

        return options['port']

    def getTableAndOpName(self,hcommand, nodePath):
        ''' get the Table (parent network type) and the HDA type name used by otcontentadd '''
        tableAndOpName = '_'
        cmd = ''' %s  optype -o  %s''' %(hcommand, nodePath)
        # print ("getTableAndOpName: ",cmd)        
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()
        
        tableAndOpName = cmd_stdout.decode('ascii').strip().split('\n')[0]

        return tableAndOpName

    def getHdaContent(self,hcommand,tableAndOpName):
        ''' returns all the available tabs on the HDA which we filter to build menu list
            There are 3 main sections to support at the moment PythonModule, PythonCook, VexCode '''

        cmd = ''' %s  otcontentls %s''' %(hcommand, tableAndOpName)
        # print ("getTableAndOpName: ",cmd)        
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()

        content = cmd_stdout.decode('ascii').strip().split('\n')
        
        # Let's filter it for now
        content = [entry for entry in content if entry in ['PythonModule', 'PythonCook', 'VexCode']]
        # print ("Filter Content:", content)

        # There may be the case when creting a HDA from a subnet that the Python section is not yet created
        # Create one:
        if len(content)==0:
            content = ['PythonModule']

        return content

    def hdaRun(self,choice,hdaOptions,tunnel,tableAndOpName):
        # No support for the vex HDA in SOPs - requires to change         
        if choice!=-1:              # -1 is set when pressed ESC
            cmd = ''' %s  \"otcontentadd %s %s %s \"''' %(tunnel.hcommand, tableAndOpName, hdaOptions[choice], tunnel.filePath)
            print ("HDA update CMD",cmd)        
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            
    def run(self):

        port = self.getPort()

        h = Tunnel(self.window,port)   

        # print (h.nodeType)
        # print (h.nodePath)
        # print (h.filePath)             # path to the temporary code file
        # print (h.getCodeAsText)
        # print ('HIP',h.hipfile)
        
        if h.nodeType in ['attribwrangle', 'pointwrangle', 'volumewrangle', 'popwrangle']:                        # wrangle nodes
            cmd = ''' %s  \"opparm %s snippet \\"%s\\" \"''' %(h.hcommand, h.nodePath,h.codeAsText)    
            # print (cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_stdout, cmd_stderr = p.communicate()   

        elif h.nodeType in ['inline']:                        # inline VOPSOP - same as wrangle nodes but with different param name
            cmd = ''' %s  \"opparm %s code \\"%s\\" \"''' %(h.hcommand, h.nodePath,h.codeAsText)    
            # print (cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_stdout, cmd_stderr = p.communicate()   

        elif h.nodeType == "python":                        # python sop
            cmd = ''' %s  \"opparm %s python \\"%s\\" \"''' %(h.hcommand, h.nodePath,h.codeAsText)    # 2x backslash to have \" in terminal
 
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_stdout, cmd_stderr = p.communicate()     
        
        elif h.nodeType=="":                                # In case no node is selected
            portMesssage = '\tPort %s not opened' % h.port
            self.window.show_quick_panel(['\tNo Node selected or...', portMesssage, '\t-> run openport -a in Houdini Textport', '\t-> rerun "Tunnel Sessions" to connect to running Houdini session'], 0 ,sublime.MONOSPACE_FONT)

        else:                                                # HDA code / scripts tab
            # For hda find its type to determine what network it is suppose to go
            tableAndOpName = self.getTableAndOpName(h.hcommand,h.nodePath)

            hdaOptions = self.getHdaContent(h.hcommand,tableAndOpName)
            hdaLabels = self.getHdaContent(h.hcommand,tableAndOpName)
            print ("NTWK type: ", tableAndOpName)
            print ("HDA Options:", hdaOptions)
            info = ['','INFO:', 'File Path: {:>25s}'.format(h.hipfile), 'Node Path: {:>25s}'.format(h.nodePath), 'Node Type: {:>25s}'.format(tableAndOpName)]
            hdaLabels.extend(info)

            # TODO there is still a problem with vex otl where the
            # otcontentadd Sop/testVex VexCode /home/kuba/temp/bbbbb.vex
            # has no effect
            
            self.window.run_command('save')           # save the current sublime file
            self.window.show_quick_panel(hdaLabels, lambda id: self.hdaRun(id,hdaOptions,h,tableAndOpName) ,sublime.MONOSPACE_FONT)


class FindHoudiniSessionsCommand(sublime_plugin.WindowCommand):


    def getConfig(self, opt):
        ''' loads the config stuff'''
        plugin_path = '%s/SubTunnel' % (sublime.packages_path())
        config = '%s/config.json' % plugin_path
        
        if os.path.exists(config)==True:
            f=open(config).read()
            options = json.loads(f)

        return options[opt]
   

    def getRunnigProcesses(self):
        cmd = "top -b -n 1 | grep -i -e hescape-bin -e hmaster-bin"
        print (cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()   

        lines = cmd_stdout.decode('ascii').strip().split('\n')

        pids = []
        for line in lines:   
            line = line.strip()           # remove leading whitesaces, or split command may sometimes fail
                                          # depending on the pid id and the order they appear
            pid = line.split(' ')[0]
            pids.append(pid)


        # # convert strings to ints
        pidsInt = []
        if len(pids)>0 and pids[0]!='':
            for i in pids:
                try:
                    pidsInt.append(int(i))
                except:
                    print("Pid is not integral value:", sys.exc_info()[0], i)
                    pass
        else:
            print ("...No Pids")    
        
        # return pids
        return pidsInt

    def getLastOpenPort(self, pid):
        cmd = "lsof -a -p%s -i4" % pid
        print (cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()   

        ports = cmd_stdout.decode('ascii').strip().split('\n')
        for port in ports:
            print (port)

        # get the last open port where the '*:' !!! this may not be portable !!!
        # Houdini starts up with a few open port but non of them are open to hcommand tool

        # Option 2  - TODO need to add timeout in case the port from houdini has not been opened
        # (Above may not be needed if below works len(ports_list)<=1 )
        # In this case hcommand is retrying and the subprocess waits indefinitely
        # As a temporary solution (This is optimal for now) we can narrow down the search port <30000
        # TODO on other machines what is the safe port threshold not to interfere with other open houdini ports             
        
        openport = None
        ports_list = []
        for port in ports:
            # print (port)
            if port.find('*:')!=-1:
                openport = int(port.split('*:')[1].split(' ')[0])
                ports_list.append(openport)

        # make sure the openport -a command has been call beforehand
        # otherwise the only open ports on houdini's end are:
        #  TCP *:52453 (LISTEN)               ----> No Response
        #  TCP localhost:14726 (LISTEN)       ----> ignored by SubTunnel

        # The proper list of ports should look as follow,
        # TCP *:52453 (LISTEN)
        # TCP *:28258 (LISTEN)
        # TCP localhost:14726 (LISTEN)

        # Note that with openport -a houdini reuses already open port
        # and doesn't start a new one

        ports_list = sorted(ports_list)
        if len(ports_list)<=1:
            openport = None
        else:
            openport = ports_list[0]         # sort and pick up the lowest number


        print (openport)

        if openport == None:
            print ("Houdini session %s has no openport" % pid)
        else:
            print ("found open %s " % openport)

        return openport



    def getHipName(self, port):

        hcommand = '%s' % self.getConfig('hcommand')

        cmd = '''%s %s echo \\`\\$HIPNAME''' % (hcommand, port)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()   

        hipname = None
        hipname = cmd_stdout.decode('ascii').strip()
        
        return hipname
    

    def savePort(self, choice, pidsDict):

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


    def run(self):

        pids = self.getRunnigProcesses()
        # print ('PIDs',pids)
        
        pidsDict={}
        # session
        for pid in pids:
            ports = {'port':-1,'hipfile':''}         # pids ports
            port = self.getLastOpenPort(pid)
         
            ports['port']=port
            ports['hipfile']=self.getHipName(port)
            
            pidsDict[pid] = ports

        
        # Build a menu options list
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

        # pidsDict consist all the collected information
        print ("All Pids:", pidsDict)
        self.window.show_quick_panel(portName_list, lambda id:  self.savePort(id,pidsDict) ,sublime.MONOSPACE_FONT)
             

        print ("Port Set")
        pass
