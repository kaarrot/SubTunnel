SubTunnel
=========

A **Sublime 3** plugin to send code snippets into running Houdini session.
supported nodes:
* SOP - vex: attribwrangle, pointwrangle, volumewrangle, popwrangle, VOPSOP (inline), python: 'python' node (new in H13)
* OTLS: code/script tabs in any context (SOP,OBJ,ROP ...) 
* Shelftools

## Overview ##
https://vimeo.com/103876297

## Get the plugin ##

- cd directory to:
  - Linux
  	- cd $HOME/.config/sublime_text_3/Packages
  - OSX:
    - cd $HOME/Library/Application\ Support/Sublime\ Text\ 3/Packages

- Then either directly clone the github repo (recommended):
  - git clone https://github.com/kubaroth/SubTunnel.git

- or:
  - download zip file 
  - put it in the ~/.config/sublime-text-3/Packages folder (at least on Linux)
  - rename SubTunnel-master to SubTunnel

Before calling the plugin for the first time make sure to update the path to hcustom in the config.json. The hcustom is located in $HFS/bin.

```
Example locations:
 Linux:
 	/opt/hfs13.0.237/bin/hcommand
 OSX:
 	/Library/Frameworks/Houdini.framework/Resources/bin/hcommand
 Windows:
 	"\"C:\\Program Files\\Side Effects Software\\Houdini 9.0.858\\bin\\hcommand\""
```

## Key Bindings ##
 ctrl+alt+]                    - Connects to running Houdini session   
 ctrl+alt+enter                - Sends code snippet to a node
 ctrl+alt+\                    - Sends code snippet to a shelf tool


## Windows Setup ##

A few more steps are requitred to get started on Windows
Make sure you have latest python 3.4 installed
* download python 3.4.1: https://www.python.org/downloads/
* Update python build for sublime:
* C:\Documents and Settings\standard\Desktop\Sublime Text Build 3059 x64\Data\Packages\User\Python3-win.sublime-build

If you just installed sublime in ..\Data\Packages\User\
create **Python3-win.sublime-build** file with:
``` 
 {
 "cmd": ["C:\\python34\\python.exe", "-u", "$file"],
 "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
 "selector": "source.python"
 }
```

If you want clone direclty from github - get git:
* http://msysgit.github.io/
* start the git navigate where Sublime/Data/Packages folder. (In this example I am working on a portable version)
* git clone https://github.com/kubaroth/SubTunnel.git
* Update config with the proper path to hcommand
 "\"C:\\Program Files\\Side Effects Software\\Houdini 9.0.858\\bin\\hcommand\""

NOTES:
* Escaping ", \ in windows shell is a nightmare! More complex regex with a lot of escaping may not work properly on Windows. This may require further editing (escape function , case 3 - # Windows - code as text)

* When calling hcomand from windows termianal - full path has to be in double quotes 
 "C:\Program Files\Side Effects Software\Houdini 9.0.858\bin\hcommand" -h

* Windows escaping:
 C:\Documents and Settings\standard>"C:\Program Files\Side Effects Software\Houdini 9.0.858\bin\hcommand" 10865 "echo `$HIPNAME"
