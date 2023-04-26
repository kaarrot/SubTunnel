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
        self.hython_path = self.getConfig('hcommand')
        self.hcommand = '%s %s' % (self.hython_path, self.port)
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
        
        # This is just a regular hscript command you would launch from hscript shell in houdini
        hscriptCmd = r'''optype -t opfind -N /`opselectrecurse("/",0)'''
        # hscriptCmd = r'''optype -t opfind -N "/"opselectrecurse("/",0)'''  # change on WIN
        
        if os.name=='posix':
            hscriptCmd = subPorts.escape(hscriptCmd, 1)
        else:
            hscriptCmd = subPorts.escape(hscriptCmd, 2) # dont escape backticks in a shell

        # the command gets wrapped with double-quates - required by bash 
        # and prepanded with full path hcommand
        cmd = r'''%s "%s"''' % (self.hcommand,hscriptCmd)
        print ("CMD getNodeType:", cmd)
    
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()           
        
        selection = None
        selection = cmd_stdout.decode('ascii').strip()

        if selection == '':
            print ("=== nothing selected ===")
        
        print ("Node type: " ,selection)

        return selection

    def getNodePath(self):
        ''' get the node path '''
        # cmd = ''' %s "opfind -N \"/\"\`opselectrecurse(\\"/\\",0)\`" ''' % self.hcommand      # no space between \"/\"\`o
        # cmd = r''' %s "opfind -N "/"\`opselectrecurse(\"/\",0)\`" ''' % self.hcommand      # raw works too

        hscriptCmd = r'''opfind -N "/"`opselectrecurse("/",0)''' # Hscript command
        
        if os.name=='posix':
            hscriptCmd = subPorts.escape(hscriptCmd, 1)
        else:
            hscriptCmd = subPorts.escape(hscriptCmd, 2)

        cmd = r'''%s "%s"''' % (self.hcommand,hscriptCmd)

        print ("CMD getNodePath:", cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()    

        nodePath = cmd_stdout.decode('ascii').strip()  
        print ("Node path: " ,nodePath) 
        
        return nodePath

    def getFilePath(self):
        view = self.window.active_view()
        return view.file_name()            # None if the file is not save


    def getCodeAsText(self):
        ''' Introduce escape characters to avoid misinterpretation by the shell '''

        view = self.window.active_view()
        codeText = view.substr(sublime.Region(0, view.size()))

        # Treat \n in the strings differently then new lines at the end of the line
        temp = []
        textSplited = re.split('((?s)".*?")', codeText)
        # textSplited = re.split('^.*$[\n]"', codeText)

        for x in textSplited:
            if os.name=='posix':
                x = subPorts.escape(x)
            else:
                x = subPorts.escape(x,3)   # WIN - code as text
            

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

    def buildPowershellCmd(self, h, hscriptCmd):
        """This is method addresses limitation of CMD which has been truncating sent source code.
        We We no longer launch CMD from subprocess, instead on Windows we use Powershell.
        """

        # NOTE: We cant rely on tempfile.gettempdir() as it returns lower case path.
        #       Since this is Windows only - access env variable directly.
        os_temp_dir = os.getenv("TEMP")
        serialized_code_file = '{0}/sublime_houdini_tunnel.txt'.format(os_temp_dir)
        
        with open(serialized_code_file, 'w') as f:
            f.write('"{0}"'.format(hscriptCmd)) # wrap output in double quotes

        # print("serialize opparm args into: ", serialized_code_file)

        # Build path to the Powershell script - same location as this script
        this_dir = os.path.split("{0}".format(__file__))[0]
        # NOTE: Subsequent arguments after PORT are serialized into a file - as this is the only way to handle 
        #       quotes and escape sequences in the source code.
        cmd = '''powershell -File "{0}/tunnel_houdini.ps1" {1} {2}'''.format(
            this_dir,
            h.hython_path,
            h.port
            )

        return cmd

    def hdaRun(self,choice,hdaOptions,tunnel,tableAndOpName):
        # Currently there is no support for the vex context in vex HDA SOP          
        if choice!=-1:              # -1 is set when pressed ESC

            hscriptCmd = r'''otcontentadd %s %s %s''' % (tableAndOpName, hdaOptions[choice], tunnel.filePath) # Hscript command
            hscriptCmd = subPorts.escape(hscriptCmd, 1)
            cmd = r'''%s "%s"''' % (tunnel.hcommand,hscriptCmd)

            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            
    def run(self):

        port = subPorts.getPort()

        h = Tunnel(self.window,port)   

        # print (h.nodeType)
        # print (h.nodePath)
        # print (h.filePath)             # path to the temporary code file
        # print (h.getCodeAsText)
        # print ('HIP',h.hipfile)
        
        if h.nodeType in ['attribwrangle', 'pointwrangle', 'volumewrangle', 'popwrangle']:  # VEX WRANGLE nodes


            hscriptCmd = r'''opparm %s snippet \"%s\"''' % (h.nodePath,h.codeAsText) # Hscript command + \"  around already escaped code
            # hscriptCmd = subPorts.escape(hscriptCmd, 1)                            # No espcing here - the code already is escaped
            cmd = r'''%s "%s"''' % (h.hcommand,hscriptCmd)

            # cmd = ''' %s  \"opparm %s snippet \\"%s\\" \"''' %(h.hcommand, h.nodePath,h.codeAsText)    

            if os.name in ['nt']:
                cmd = self.buildPowershellCmd(h, hscriptCmd)

            print ("CMD - vexsop:", cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_stdout, cmd_stderr = p.communicate()   

        elif h.nodeType in ['inline']:                       # INLINE VEX VOPSOP - same as wrangle nodes but with different param name
            # cmd = ''' %s  \"opparm %s code \\"%s\\" \"''' %(h.hcommand, h.nodePath,h.codeAsText)    
            
            hscriptCmd = r'''opparm %s code \"%s\"''' % (h.nodePath,h.codeAsText)  # just and escape around codeAsText                         
            cmd = r'''%s "%s"''' % (h.hcommand,hscriptCmd)

            print ("CMD inline:", cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_stdout, cmd_stderr = p.communicate()   

        elif h.nodeType == "python":                        # PYTHON SOP
            # cmd = ''' %s  \"opparm %s python \\"%s\\" \"''' %(h.hcommand, h.nodePath,h.codeAsText)    # 2x backslash to have \" in terminal

            hscriptCmd = r'''opparm %s python \"%s\"''' % (h.nodePath,h.codeAsText)  # just and escape around codeAsText                          
            cmd = r'''%s "%s"''' % (h.hcommand,hscriptCmd)

            if os.name in ['nt']:
                cmd = self.buildPowershellCmd(h, hscriptCmd)

            print ("CMD python sop:", cmd)
 
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
        
        
        if os.name=='posix':
            pidsDict={}

            pids = subPorts.getHoudiniPorts()
            
            for pid,port in pids.items():
                ports = {'port':-1,'hipfile':''}         # pids ports
                ports['port']=port
                ports['hipfile']=subPorts.getHipName(port)
                pidsDict[pid] = ports

        else:
            pidsDict = {}
            import SubTunnel.SubTunnelPortsWin as subWinPorts
            from imp import reload
            reload(subWinPorts)
            pidsDict = subWinPorts.getHPorts()


        
        print ("---", pidsDict)
                
        portName_list = subPorts.buildPortList(pidsDict) # Build list 

        # pidsDict consist all the collected information
        print ("All Pids:", pidsDict)
        self.window.show_quick_panel(portName_list, lambda id:  subPorts.savePort(id,pidsDict) ,sublime.MONOSPACE_FONT)
             
        print ("Port Set")

        
        pass

class ShelfToolCommand(sublime_plugin.WindowCommand):
    '''
        Send the code into one of the existing shelf tools
        Name the tool has to set before
    '''

    def on_done(self, shelfToolName):

        ### Update config with new tool name
        configAll = subPorts.getConfig()
        configAll['shelftool'] = shelfToolName
        # print(configAll)

        plugin_path = '%s/SubTunnel' % (sublime.packages_path())
        config = '%s/config.json' % plugin_path
        f = open(config, 'w')
        f.write(json.dumps(configAll))
        f.close()

        ### Send the code
        port = subPorts.getPort()
        h = Tunnel(self.window,port) 

        code = h.codeAsText
        python = "hou.shelves.tools()['%s'].setData('%s')" % (shelfToolName,code)
        hscriptCmd = r'''python -c \"%s\"''' % python
        

        cmd = r'''%s "%s"''' % (h.hcommand,hscriptCmd)

        print ("CMD shelf:", cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = p.communicate()  


    def run(self):

        prevShelfTool = subPorts.getConfig('shelftool')
        print (prevShelfTool)
        if prevShelfTool == None:
            prevShelfTool="_"

        self.window.show_input_panel("Shelf Tool Name:",prevShelfTool,self.on_done,None,None)
        # self.window.show_quick_panel(portName_list, lambda id:  subPorts.savePort(id,pidsDict) ,sublime.MONOSPACE_FONT)




        pass
