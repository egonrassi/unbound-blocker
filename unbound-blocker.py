#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" 
Unbound Blocker
Middleware to read a public list of domains to block in the
Unbound resolver without needing a restart.
Utilizes the unbound-control interface.

"""

import argparse, requests, validators, logging, sys, re
from unbound_console import RemoteControl

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def main(args):
  #Define const
  currentlist=[]
  freshlist=[]
  remove_bulk = []
  add_bulk = []

  # Get a fresh list of domains to block - expect multiple input arguments
  for urlinput in args.input:
    try:
      r = requests.get(urlinput[0])
    except requests.exceptions.RequestException as e:
      raise SystemExit(e)

    for blocklist in r.text.split("\n"):
      if not validators.domain(blocklist):
        continue
      if args.ignore:
        for ignlist in args.ignore:
          if re.search(ignlist[0], blocklist):
            break
        else:
          freshlist.append(blocklist)
      else:
        freshlist.append(blocklist)

  # Connect to Unbound Control
  rc = RemoteControl(host=args.ubhost, port=args.ubport,
                    server_cert = args.ubservercert,
                    client_cert= args.ubclientcert,
                    client_key= args.ubclientkey)

  # Get the current state
  o = rc.send_command(cmd="list_local_zones")
  for localzone in o.split("\n"):
    if localzone.find("always_nxdomain")!=-1:
      currentlist.append((localzone.split(". ")[0]))

  # Run diffs - exit if no changes are needed
  difference_toremove = list(set(currentlist) - set(freshlist))
  difference_toadd = list(set(freshlist) - set(currentlist))
  changes=len(difference_toremove) + len(difference_toadd)
  if changes == 0:
      logging.info("No differences detected. No need to continue - exiting.")
      sys.exit(0)
  else:
      logging.info("Being blocked but not in list: " + str(difference_toremove))
      logging.info("Currently not blocked: " + str(difference_toadd))

  # Commit changes if argument commit is true and changes need to be made
  if args.commit == True and changes != 0:
    #Remove missing zones
    for remove_zone in difference_toremove:
      remove_bulk.append( remove_zone )
    # Add missing zones
    for add_zone in difference_toadd:
      add_bulk.append( add_zone + " always_nxdomain")
    logging.info("Committing changes")
    # Commit changes to Unbound
    o = rc.send_command(cmd="local_zones_remove", data_list=remove_bulk)
    o = rc.send_command(cmd="local_zones", data_list=add_bulk)

if __name__ == '__main__':
  # Parse args
  parser = argparse.ArgumentParser(description='Block domains in Unbound through a public list')
  parser.add_argument('--input', dest='input', action='append', nargs='+', required=True, help='URL to the public list for domains to block - Multiple arguments allowed')
  parser.add_argument('--unboundhost', dest='ubhost', default='localhost', help='Unbound Control server address or hostname')
  parser.add_argument('--unboundport', dest='ubport', default=8953, type=int, help='Unbound Control server port')
  parser.add_argument('--unboundservercert', dest='ubservercert', default='/etc/unbound/unbound_server.pem', help='Unbound Control Server Certificate')
  parser.add_argument('--unboundclientcert', dest='ubclientcert', default='/etc/unbound/unbound_control.pem', help='Unbound Control Client Certificate')
  parser.add_argument('--unboundclientkey', dest='ubclientkey', default='/etc/unbound/unbound_control.key', help='Unbound Control Client Certificate key')
  parser.add_argument('--commit', dest='commit', action='store_true', required=False, help='Commit changes if any')
  parser.add_argument('--ignore', dest='ignore', action='append', nargs='+', required=False, help='Ignore domains - Regex syntax')
  args = parser.parse_args()

  main(args)
  sys.exit(0)