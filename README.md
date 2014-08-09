SubTunnel
=========

A Sublime plugin to send code snippets into running Houdini session.
supported nodes:
    SOP - vex: attribwrangle, pointwrangle, volumewrangle, popwrangle, VOPSOP (inline)
          python: 'python' node (new in H13)
    OTLS: code/script tabs in any context (SOP,OBJ,ROP ...) 


Before calling the plugin for the first time make sure to update 
the path hcustom in config.json

Example locations of hcustom:

Linux:
	/opt/hfs13.0.237/bin/hcommand
OSX:
	/Library/Frameworks/Houdini.framework/Resources/bin/hcommand
Windows:
	TBD


##### Windows #####

download git: http://msysgit.github.io/
download python 3.4.1: https://www.python.org/downloads/

git clone https://github.com/kubaroth/SubTunnel.git

Make sure to update python build for sublime:
C:\Documents and Settings\standard\Desktop\Sublime Text Build 3059 x64\Data\Packages\User\Python3-win.sublime-build

If you just installed sublime in ..\Data\Packages\User\
create: Python3-win.sublime-build file and put:
{
	"cmd": ["C:\\python34\\python.exe", "-u", "$file"],
	"file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
	"selector": "source.python"
}


edit SubTunel config
"\"C:\\Program Files\\Side Effects Software\\Houdini 9.0.858\\bin\\hcommand\""

Call from the 
"C:\Program Files\Side Effects Software\Houdini 9.0.858\bin\hcommand" -h

# windows escaping
C:\Documents and Settings\standard>"C:\Program Files\Side Effects Software\Houdini 9.0.858\bin\hcommand" 10865 "echo `$HIPNAME"