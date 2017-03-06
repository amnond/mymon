from subprocess import Popen, PIPE
command = 'ps -eo size,pid,user,command'.split()
process = Popen(command, stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()

for line in stdout.splitlines():
    print(">>>"+line)



