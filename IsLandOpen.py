import sys, os, math, random ,time	 
import threading
import psutil
import subprocess
class IsLandThread(threading.Thread):
	def __init__(self):
		super(IsLandThread,self).__init__()



	def run(self):
		if sys.path[0].startswith("C:\\"):
			cmd1='cd %s'%sys.path[0]
		else:
			root=sys.path[0][:3]
			cmd1='cd /d %s'%root+" & "+'cd %s'%sys.path[0]
			
		cmd2='IsLand\\KinectSandbox.exe'
		cmd3='	%s &&\
						%s '%(cmd1,cmd2)
						
		os.system(cmd3)

		pid = psutil.Process().children(recursive=True)[0].pid
		# 获取进程路径
		path = self.get_process_path(pid)

		print(path)
		return path
	def get_process_path(pid):
		try:
			process = psutil.Process(pid)
			path = process.exe()
			return path
		except psutil.NoSuchProcess:
			print("Process with pid {} does not exist".format(pid))

	def kill_process_by_path(path):
		# 使用 pidof 命令获取指定路径下的进程 ID
		pid = subprocess.check_output(['pidof', path]).strip()
		# 使用 kill 命令杀掉进程
		subprocess.run(['kill', '-9', pid], shell=True)
		subprocess.run(['kill', '-9', pid], shell=True)

# 关闭进程
#os.system('taskkill /f /t /im '+exe_name)#MESMTPC.exe程序名字