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