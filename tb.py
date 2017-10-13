#!/usr/bin/python
# coding: UTF-8

import commands
import os
import sys
import time

#print '*'*20
#print os.getcwd() #假设是A执行了tb.py,则打印A的所在路径(以tb.py结尾)
#print '*'*20
#print sys.path[0] #打印tb.py的路径(不以tb.py，以tb.py的父亲的路径结尾)
#print '*'*20
#print sys.argv[0] #打印tb.py的路径,相对路径执行脚本则会返回相对路径,绝对路径执行脚本则返回绝对路径(以tb.py结尾)
try:
	print time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())),
	b=sys.path[0]
	os.chdir(b)


	#a,b=commands.getstatusoutput("pwd")
	#print a,b

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

	print ":	success"
    
except Exception, e:
    print 'str(Exception):\t', str(e)+'————',