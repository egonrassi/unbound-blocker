#!/usr/bin/env python3

# EgonRassi Unbound Blocker from list

import argparse,requests

#Define const
currentlist=[]
freshlist=[]
remove_bulk = []
add_bulk = []

# Parse args
parser = argparse.ArgumentParser(description='Block domains in Unbound through a public list')
parser.add_argument('--input', dest='input',action='append',nargs='+', required=True,help='URL to the public list for domains to block - This can have multiple instances')
parser.add_argument('--unboundhost', dest='ubhost', default='localhost', help='Unbound Control server address or hostname')
parser.add_argument('--unboundport', dest='ubport', default=8953, type=int, help='Unbound Control server port')
parser.add_argument('--unboundservercert', dest='ubservercert', default='/etc/unbound/unbound_server.pem', help='Unbound Control Server Certificate')
parser.add_argument('--unboundclientcert', dest='ubclientcert', default='/etc/unbound/unbound_control.pem', help='Unbound Control Client Certificate')
parser.add_argument('--unboundclientkey', dest='ubclientkey', default='/etc/unbound/unbound_control.key', help='Unbound Control Client Certificate key')
parser.add_argument('--commit', dest='commit', action='store_true', required=False,help='Commit changes if any')
args = parser.parse_args()

# Connect to Unbound Control
from unbound_console import RemoteControl
rc = RemoteControl(host=args.ubhost, port=args.ubport,
                   server_cert = args.ubservercert,
                   client_cert= args.ubclientcert,
                   client_key= args.ubclientkey)

# Get the input - expect multiple lists
for urlinput in args.input:
 try:
    r = requests.get(urlinput[0])
 except requests.exceptions.RequestException as e:
    raise SystemExit(e)

 for bllist in r.text.split("\n"):
    if bllist != "":
      freshlist.append(bllist)

# Get the current state
o = rc.send_command(cmd="list_local_zones")
for localzone in o.split("\n"):
    if localzone.find("always_nxdomain")!=-1:
     currentlist.append((localzone.split(". ")[0]))

# Run diffs
difference_toremove = list(set(currentlist) - set(freshlist))
difference_toadd = list(set(freshlist) - set(currentlist))
changes=len(difference_toremove) + len(difference_toadd)
if changes == 0:
    print("No differences detected")
else:
    print("Being blocked but not in list: " + str(difference_toremove))
    print("Currently not blocked: " + str(difference_toadd))

# Commit changes if argument commit is true and changes need to be made
if args.commit == True and changes != 0:
 for remove_zone in difference_toremove:
   remove_bulk.append( remove_zone )

 for add_zone in difference_toadd:
   add_bulk.append( add_zone + " always_nxdomain")
 print("Committing changes")

 o = rc.send_command(cmd="local_zones_remove", data_list=remove_bulk)
 o = rc.send_command(cmd="local_zones", data_list=add_bulk)
