from subprocess import Popen, PIPE
#import platform

scommand = 'ps aux'
cols = (5,10)
#if platform.system() == 'Darwin':
#    scommand = 'ps aux'
#    cols = (5, 10)
command = scommand.split()

process = Popen(command, stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()

out = stdout.splitlines()
total = len(out)
maxproclen = 85
proclist = []
for i in range(1,total):
    line = out[i]
    sline = line.split()
    mem = sline[cols[0]].decode('utf-8')
    proc = ' '.join([x.decode('utf-8') for x in sline[cols[1]:]])
    if len(proc) > maxproclen:
        proc = proc[0:maxproclen]+'...';
    procinfo = (mem, proc)
    proclist.append(procinfo)
proclist.sort(key=lambda tup: int(tup[0]))
for proc in proclist:
   print( '%s %s' % proc)
