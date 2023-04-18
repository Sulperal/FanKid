import sys, os, math, random ,time	 
import threading

# 火山喷发
class VolcanicEruption(threading.Thread):
	def __init__(self):
		super(VolcanicEruption,self).__init__()
	def run(self):
		if sys.path[0].startswith("C:\\"):
			cmd1='cd %s'%sys.path[0]
		else:
			root=sys.path[0][:3]
			cmd1='cd /d %s'%root+" & "+'cd %s'%sys.path[0]
			
		cmd2='Land\\KinectSandbox.exe'
		cmd3='	%s &&\
						%s '%(cmd1,cmd2)
						
		os.system(cmd3)



	




