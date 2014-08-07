"""
SubTunnel
Kuba Roth: 140801
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
import time

import SubTunnel.SubTunnelPorts as subPorts

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
        ''' loads the config '''
        plugin_path = '%s/SubTunnel' % (sublime.packages_path())
        config = '%s/config.json' % plugin_path
        
        if os.path.exists(config)==True:
            f=open(config).read()
            options = json.loads(f)

        return options[opt]

    def getNodeType(self):
        ''' get the selected node type '''
        # Note a special treatment of backticks (bash specifics)
        # cmd = ''' %s "optype -t opfind -N \"/\"\`opselectrecurse(\\"/\\",0)\`" ''' % self.hcommand
        cmd = r''' %s "optype -t opfind -N "/"\`opselectrecurse(\"/\",0)\`" ''' % self.hcommand   # raw works too

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
        ''' get the node path '''
        # cmd = ''' %s "opfind -N \"/\"\`opselectrecurse(\\"/\\",0)\`" ''' % self.hcommand      # no space between \"/\"\`o
        cmd = r''' %s "opfind -N "/"\`opselectrecurse(\"/\",0)\`" ''' % self.hcommand      # raw works too

        #print (cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()           
        
        return cmd_stdout.decode('ascii').strip()

    def getFilePath(self):
        view = self.window.active_view()
        return view.file_name()            # None if the file is not save

    def escape(self, s):
        ''' Special cases - escaping required for correct parsing in the shell '''

        s = s.replace(r"\n", r"\\\\n")         # escape new line inside the quotes

        s = s.replace(r'$',r'\$')
        s = s.replace(r'@',r'\@')
        s = s.replace(r'#',r'\#')
        s = s.replace(r'%',r'\%')
        s = s.replace(r'^',r'\^')
        s = s.replace(r'&',r'\&')
        s = s.replace(r'`',r'\`')

        # s = s.replace(r"'",r"\'")
        # s = s.replace(r'"',r'\"')

        s=s.replace("\n", "\\n")
        
        s=s.replace(r'"', r'\\\"')    # previously # s=s.replace("\"", "\\\\\\\"")

        return s


    def getCodeAsText(self):
        ''' Introduce escape characters to avoid misinterpretation by the shell '''

        view = self.window.active_view()
        codeText = view.substr(sublime.Region(0, view.size()))

        # Treat \n in the strings differently then new lines at the end of the line
        temp = []
        textSplited = re.split('((?s)".*?")', codeText)
        for x in textSplited:
            x = self.escape(x)

            temp.append(x)
        codeText = r''.join(temp)


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
        content = [entry for entry in content if entry in ['PythonModule', 'PythonCook', 'VflCode']]
        # print ("Filter Content:", content)

        # There may be the case when creting a HDA from a subnet that the Python section is not yet created
        # Create one:
        if len(content)==0:
            content = ['PythonModule']

        return content

    def hdaRun(self,choice,hdaOptions,tunnel,tableAndOpName):
        # Currently there is no support for the vex context in vex HDA SOP          
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
    '''
        This section allows user to pick the desired Houdini session to connect to
    '''

    def run(self):
        
        pidsDict={}

        pids = subPorts.getHoudiniPorts()
        
        for pid,port in pids.items():
            ports = {'port':-1,'hipfile':''}         # pids ports
            ports['port']=port
            ports['hipfile']=subPorts.getHipName(port)
            pidsDict[pid] = ports


        print ("---", pidsDict)
                
        portName_list = subPorts.buildPortList(pidsDict) # Build list 

        # pidsDict consist all the collected information
        print ("All Pids:", pidsDict)
        self.window.show_quick_panel(portName_list, lambda id:  subPorts.savePort(id,pidsDict) ,sublime.MONOSPACE_FONT)
             
        print ("Port Set")
        pass
        
        