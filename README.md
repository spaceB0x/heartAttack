heartAttack
===========

A simple to use PoC to automatically check and exploit the heartbleed vulnerablility.
This is intended for Network Admins, Security Folk, home users, or anyone on the webz.
Finally proove once and for all that Heartbleed is/isn't on your network. 
Then find something else to talk about ;)

Note: This will install and configure 'Masscan' if it isn't already in your current directory. If this
	fails to 'make' the first time, just try it again. This a bug I am trying to work out.

Parameters:

	-h, --help	Help
	-i		IP address or range
	-w		File to write output to
	-p 		Port(s) to scan. Defaults to 443
	-u		Unused IP in VLAN. MUST have. Masscan needs an unused ip from your network.
	-m		MODE. 

