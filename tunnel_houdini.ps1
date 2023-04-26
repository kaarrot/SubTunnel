# Example of starting hython from command line Powershell:
# 
# Start-Process -FilePath 'c:/Program Files/Side Effects Software/Houdini 18.5.694/bin/hcommand.exe' -Wait -PassThru -NoNewWindow -ArgumentList "22881 opparm /obj/geo1/python1 python 'aaa dddd'"
#

param([Parameter(Mandatory=$True)]
      [string]$HYTHON_PATH,
      [string]$PORT
    )

# Read back the serialized code. 
$code=Get-Content $env:TEMP/sublime_houdini_tunnel.txt

# Debug
#echo Start-Process -FilePath $HYTHON_PATH -Wait -PassThru -NoNewWindow -ArgumentList "$code"

Start-Process -FilePath $HYTHON_PATH -Wait -PassThru -NoNewWindow -ArgumentList "$PORT $code"
