#!/usr/bin/python3

import argparse
import requests
import json
import os
import teamsenum.auth
import time
import threading
from teamsenum.auth import p_success, p_err, p_warn, p_normal, p_info
from teamsenum.enum import TeamsUserEnumerator

def banner(__version__):
   print(r"""
 _______                       ______
|__   __|                     |  ____|
   | | ___  __ _ _ __ ___  ___| |__   _ __  _   _ _ __ ___
   | |/ _ \/ _` | '_ ` _ \/ __|  __| | '_ \| | | | '_ ` _ \
   | |  __/ (_| | | | | | \__ \ |____| | | | |_| | | | | | |
   |_|\___|\__,_|_| |_| |_|___/______|_| |_|\__,_|_| |_| |_|

   v%s developed by %s
   %s
   """ % (__version__, "@_bka_", "SSE | Secure Systems Engineering GmbH"))

def enumerate_user(enum, email, accounttype, presence, outfile):
   enum.check_user(email.strip(), accounttype, presence=presence, outfile=outfile)

def enumerate_guid(enum, guid, outfile):
   enum.check_guid(guid.strip(), outfile=outfile)


if __name__ == "__main__":
   """
   Main entrypoint. Parses command line arguments and invokes login and enumeration sequence.

   Args:
      argv (str []): Command line arguments passed to this script

   Returns:
      None
   """
   __version__ = "1.0.3"

   banner(__version__)
   parser = argparse.ArgumentParser()

   parser.add_argument('-a', '--authentication', dest='authentication', choices=['devicecode','password','token','credfile'], required=True, help='')
   parser.add_argument('-u', '--username', dest='username', type=str, required=False,  help='Username for authentication')
   parser.add_argument('-p', '--password', dest='password', type=str, required=False, help='Password for authentication')
   parser.add_argument('-o', '--outfile', dest='outfile', type=str, required=False, help='File to write the results to')

   parser.add_argument('-d', '--devicecode', dest='devicecode', type=str, required=False, help='Use Device code authentication flow')

   parser.add_argument('-s', '--skypetoken',  dest='skypetoken',  type=str, required=False, help='Skype specific token from X-Skypetoken header. Only required for personal accounts')
   parser.add_argument('-t', '--accesstoken', dest='bearertoken', type=str, required=False,  help='Bearer token from Authorization: Bearer header. Required by teams and live.com accounts')

   parser.add_argument('--delay', dest='delay', type=int, required=False, default=0, help='Delay in [s] between each attempt. Default: 0')

   parser_inputdata_group = parser.add_mutually_exclusive_group(required=True)
   parser_inputdata_group.add_argument('-e', '--targetemail', dest='email', type=str, required=False, help='Single target email address')
   parser_inputdata_group.add_argument('-f', '--file', dest='file', type=str, required=False, help='Input file containing a list of target email addresses')
   parser_inputdata_group.add_argument('-g', '--guids', dest='guids', type=str, required=False, help='Input file containing a list of user Object ID GUIDs')

   parser.add_argument('-n', '--threads', dest='num_threads', type=int, required=False, default=7, help='Number of threads to use for enumeration. Default: 7')
   parser.add_argument("-v", "--verbose", help="enable verbose output", action='store_true')
   parser.add_argument("-db", "--database", help="enable logging to remote database (optional connection string)", type=str, nargs='?', const='db.conf', default=None)
   parser.add_argument("-se", "--session", help="add a session name/tag for remote database (8 char max)", type=str, nargs='?', default='default')

   args = parser.parse_args()
   session = "default"

   if args.outfile:
      fd = teamsenum.utils.open_file(args.outfile)
   else:
      fd = None

   if args.database:
      if args.database == '':
         db_file = 'db.conf'
      else:
         db_file = args.database

      if args.session:
         session = args.session
      else:
         session = "default"

      # check for database.conf
      if os.path.isfile(db_file):
         try:
            #this can take a value of filename
            #check_db_conf()
            print("DB LOGGING = TRUE")
            #db_logging = True
            db_logging = db_file
         except:
            db_logging = False
   else:
      print("DB LOGGING = FALSE")
      db_logging = False


   if args.authentication == "credfile":
      # check for the file specified
      if not os.path.isfile(args.authentication):
         print(f"Error: credfile does not exist at {args.authentication}")
         exit


   accounttype, bearertoken, skypetoken, teams_enrolled, refresh_token, auth_app, auth_metadata = teamsenum.auth.do_logon(args)
   enum = TeamsUserEnumerator(skypetoken, bearertoken, teams_enrolled, refresh_token, auth_app, auth_metadata, db_logging, session)


   if args.email or args.file:
      if args.email:
         emails = [args.email]

      if args.file:
         with open(args.file) as f:
            emails = f.readlines()

      p_info("Starting user enumeration\n")
      threads = []
      for email in emails:
         time.sleep(args.delay)
         thread = threading.Thread(target=enumerate_user, args=(enum, email, accounttype, True, fd))
         threads.append(thread)
         thread.start()

         # Limit the number of active threads
         if len(threads) >= args.num_threads:
            for t in threads:
               t.join()
            threads = []

   if args.guids:
      with open(args.guids) as f:
         guids = f.readlines()

      p_info("Starting user enumeration\n")
      threads = []
      for guid in guids:
         time.sleep(args.delay)
         thread = threading.Thread(target=enumerate_guid, args=(enum, guid, fd))
         threads.append(thread)
         thread.start()

         # Limit the number of active threads
         if len(threads) >= args.num_threads:
            for t in threads:
               t.join()
            threads = []


   # Wait for the remaining threads to finish
   for thread in threads:
      thread.join()

   if fd:
      fd.close()
