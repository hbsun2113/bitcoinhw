#!/usr/bin/python
import commands
a,b=commands.getstatusoutput("git add .")
if a!=0:
	print "error in add:"+b
	exit()
a,b=commands.getstatusoutput(''' git commit -m "nothing" ''')
if a!=0:
	print "error in commit:"+b
	exit()
a,b=commands.getstatusoutput("git push")
if a!=0:
	print "error in push:"+b
	exit()
print "success"