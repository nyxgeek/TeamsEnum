#!/usr/bin/python3

from datetime import datetime, date
import requests
import json
from teamsenum.utils import p_success, p_err, p_warn, p_normal, p_file, remove_html_preserve_newlines, check_db_conf, log_presence_db, log_ooo_db, sanitize_and_truncate, calculate_md5, log_userinfo_db
from teamsenum.auth import logon_with_accesstoken

class TeamsUserEnumerator:
   """ Class that handles enumeration of users that use Microsoft Teams either from a personal, or corporate account  """

   def __init__(self, skypetoken, bearertoken, teams_enrolled, refresh_token, auth_app, auth_metadata, db_logging, session):
      """
      Constructor that accepts authentication tokens for use during enumeration

      Args:
         skypetoken (str): Skype access token
         bearertoken (str): Bearer token for Teams
         teams_enrolled (boolean): Flag to indicate whether the own account has a valid Teams subscription

      Returns:
         None
      """
      self.skypetoken = skypetoken
      self.bearertoken = bearertoken
      self.teams_enrolled = teams_enrolled
      self.refresh_token = refresh_token
      self.auth_app = auth_app
      self.auth_metadata = auth_metadata
      self.db_logging = db_logging
      if self.db_logging:
         self.database = check_db_conf(self.db_logging)
         print("DB LOGGING IS ON")
      self.session = session

   def check_guid(self, guid, outfile=None):
      print(f"Guid: {guid}, DB Logging: {self.db_logging}")
      self.check_teams_guid(guid,outfile)

   def check_user(self, email, type, presence=False, outfile=None):
      """
      Wrapper that either calls check_live_user or check_teams_user depending on the account type

      Args:
         email (str): Email address of the user that should be checked
         type (str): Type of the account (either 'personal' or 'corporate')
         presence (boolean): Flag that indicates whether the presence should also be checked
         outfile (str): File descriptor for writing the results into an outfile

      Returns:
         None
      """
      if type == "personal":
         self.check_live_user(email, presence, outfile)
      elif type == "corporate":
         self.check_teams_user(email, presence, outfile)

   def check_teams_user(self, email, presence=False, outfile=None, recursive_call=False):
      """
      Checks the existence and properties of a user, using the teams.microsoft.com endpoint

      Args:
         email (str): Email address of the user that should be checked
         presence (boolean): Flag that indicates whether the presence should also be checked
         outfile (str): File descriptor for writing the results into an outfile

      Returns:
         None
      """
      headers = {
         "Authorization": "Bearer " + self.bearertoken,
         "X-Ms-Client-Version": "1415/1.0.0.2023031528",
         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
      }

      user = {'email':email}
      user['exists'] = False

      content = requests.get("https://teams.microsoft.com/api/mt/emea/beta/users/%s/externalsearchv3?includeTFLUsers=true" % (email), headers=headers)
      print(content.text)
      print(content.headers)
      if content.status_code == 403:
         user['exists'] = True
         if self.teams_enrolled:
            user['info'] = "User exists but full user details can't be fetched. Either the target tenant or your tenant disallow communication to external domains."
         else:
            user['info'] = "User exists but full user details can't be fetched. You don't have a valid Teams subscription."
         p_success("%s - %s" % (email, user.get('info')))
         p_file(json.dumps(user), outfile)
         return

      if content.status_code == 401:
         if( not recursive_call and self.refresh_token ):
            p_warn("Unable to enumerate user. Trying to get a new access token...")
            result = logon_with_accesstoken(self.auth_metadata, self.auth_app)
            if( 'access_token' in result ):
               p_warn("Got new access token. Rechecking the user...")
               self.bearertoken = result['access_token']
               return self.check_teams_user(email, presence=presence, outfile=outfile, recursive_call=True)
         else:
            p_warn("Unable to enumerate user. Is the access token valid?", exit=True)

      if content.status_code != 200:
         p_warn("Unable to enumerate user %s. Invalid target email address?" % (email))
         return

      print(f"{content.text}")
      log_userinfo_db(self.database, content.text)
      user_profile = json.loads(content.text)
      user['info'] = user_profile

      if len(user_profile) > 0 and isinstance(user_profile, list):
         user['exists'] = True
         if presence and "mri" in user_profile[0]:
            print("----- Performing additional lookup --- ")
            mri = user_profile[0].get('mri')
            print(f"MRI: {mri}")
            presence = self.check_teams_guid(mri)
            #presence = self.check_teams_presence(mri)
            user['presence'] = presence
         result_stdout = "%s - %s" % (email, user.get('info')[0].get('displayName'))
         result_stdout += "" if not presence else " (%s, %s)" % (user.get('presence')[0].get('presence').get('availability'), user.get('presence')[0].get('presence').get('deviceType'))
         p_success(result_stdout)
      else:

         user['info'] = "Target user not found. Either the user does not exist, is not Teams-enrolled or is configured to not appear in search results (personal accounts only)"
         p_warn("%s - %s" % (email, user.get('info')))

      print(f"{json.dumps(user)}")
      p_file(json.dumps(user), outfile)

   def check_live_user(self, email, presence=False, outfile=None):
      """
      Checks the existence and properties of a user, using the teams.live.com endpoint

      Args:
         email (str): Email address of the user that should be checked
         presence (boolean): Flag that indicates whether the presence should also be checked
         outfile (str): File descriptor for writing the results into an outfile

      Returns:
         None
      """
      headers = {
         "Content-Type": "application/json",
         "Authorization": "Bearer " + self.bearertoken,
         "X-Skypetoken": self.skypetoken
      }

      payload = {
         "emails": [email],
      }

      content = requests.post("https://teams.live.com/api/mt/beta/users/searchUsers", headers=headers, json=payload)

      if content.status_code == 400:
         p_warn("Unable to enumerate user. Is the Skypetoken valid?", exit=True)

      if content.status_code == 401:
         p_warn("Unable to enumerate user. Is the access token valid?", exit=True)

      if content.status_code != 200:
         p_warn("Error: %d" % (content.status_code))
         return

      json_content = json.loads(content.text)

      if len(json_content) == 0:
         p_warn("Cannot retrieve information about the user %s" % (email))
         return

      for item in json_content:
         user_profile = json_content.get(item).get('userProfiles')
         user = {'email': item}
         user['exists'] = False
         user['info'] = user_profile
         if json_content.get(item).get("status") == "Success":
            user['exists'] = True
            if presence and len(user_profile) > 0 and isinstance(user_profile, list) and "mri" in user_profile[0]:
               mri = user_profile[0].get('mri')
               #presence = self.check_live_presence(mri)
               presence = self.check_teams_guid(mri,outfile)
               user['presence'] = presence
            result_stdout = "%s - %s" % (email, user.get('info')[0].get('displayName'))
            result_stdout += "" if not presence else " (%s, %s)" % (user.get('presence')[0].get('presence').get('availability'), user.get('presence')[0].get('presence').get('deviceType'))
            p_success(result_stdout)
         else:
            user['info'] = "Target user not found. Either the user does not exist, is not enrolled for Teams or disallows communication with your account"
            p_warn("%s - %s" % (item, user.get('info')))

         p_file(json.dumps(user), outfile)




   def check_teams_guid(self, guid, outfile=None, Recursive=False):
      """
      Checks the presence and properties of a teams GUID

      Args:
         guid (str): ObjectID GUID of the user that should be checked
         outfile (str): File descriptor for writing the results into an outfile

      Returns:
         None
      """

      now = datetime.now()
      unixtime = str(int(now.timestamp()))
      currentdate = now.date().isoformat()
      totalminutes = now.hour * 60 + now.minute
      qh_period = totalminutes // 15
      hh_period = totalminutes // 30

      headers = {
         "Authorization": "Bearer " + self.bearertoken,
         "X-Ms-Client-Version": "1415/1.0.0.2023031528",
         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
      }

      user = {'guid':guid}
      if guid:
         try:
            #mri = f"8:orgid:{guid}"
            #mri = guid if guid.startswith("8:orgid:") else f"8:orgid:{guid}"
            mri = guid if guid.startswith(("8:orgid:", "8:sfb:")) else f"8:orgid:{guid}"
            if guid.startswith(("8:orgid:", "8:sfb:")):
               prefix,guid = guid.split(":", 2)[1:]
            #mri = guid if guid.startswith("8:orgid:") else f"8:sfb:{guid}"
            print(f"mri: {mri}, guid: {guid}")
            presence = self.check_teams_presence(mri)
            user['presence'] = presence

         except:
            if( not self.refresh_token ):
               p_warn("Unable to enumerate user. Trying to get a new access token...")
               result = logon_with_accesstoken(self.auth_metadata, self.auth_app)
               if( 'access_token' in result ):
                  p_warn("Got new access token. Rechecking the user...")
                  self.bearertoken = result['access_token']
                  return self.check_teams_guid(guid, outfile=outfile, recursive_call=True)
            else:
               p_warn("Unable to enumerate user. Is the access token valid?", exit=True)


         """Extracts and cleans the out-of-office message if it exists."""
         for record in presence:
            # Check if 'presence' -> 'calendarData' -> 'outOfOfficeNote' exists
            ooo_note = record.get('presence', {}).get('calendarData', {}).get('outOfOfficeNote', {})
            if 'message' in ooo_note:
               ooo_enabled = 1
               raw_message = ooo_note['message']

               # Remove HTML while preserving newlines
               cleaned_message = remove_html_preserve_newlines(raw_message)
               print("\nCleaned Message (HTML Removed):")
               print(cleaned_message)
               md5sum = calculate_md5(raw_message)
               sanitized_text, truncated = sanitize_and_truncate(raw_message)
               message_length = len(raw_message)
               print(f"MD5: {md5sum}, Length: {message_length}, Truncated: {truncated}")
               print(f"{sanitized_text}")
               if self.db_logging:
                  log_ooo_db(self.database, guid, raw_message)

            else:
               ooo_enabled = 0

         devicetype = user.get('presence')[0].get('presence').get('deviceType')
         if not devicetype:
            devicetype = "Off"
         availability = user.get('presence')[0].get('presence').get('availability')

         result_stdout = "%s" % (guid)
         #result_stdout += "" if not presence else " (%s, %s)" % (user.get('presence')[0].get('presence').get('availability'), user.get('presence')[0].get('presence').get('deviceType'))
         result_stdout += "" if not presence else " (%s, %s, %s, %s,%s)" % (availability, devicetype, ooo_enabled, unixtime, qh_period)
         p_success(result_stdout)
      else:
         user['info'] = "Target user not found. Either the user does not exist, is not Teams-enrolled or is configured to not appear in search results (personal accounts only)"
         p_warn("%s - %s" % (email, user.get('info')))

      #print(f"{json.dumps(user)}")

      p_file(json.dumps(user), outfile)
      if self.db_logging:
         # log to db with db_log() from utils.py
         print("LOGGING TO DB")

         log_result = log_presence_db(
            db_config=self.database,
            teams_guid=guid,
            availability=availability,
            ooo_enabled=ooo_enabled,
            device=devicetype,
            scrape_date_unix=unixtime,
            scrape_date=currentdate,
            hh_period=hh_period,
            qh_period=qh_period,
            session=self.session
         )

         if log_result:
            print("Data logged successfully.")
         else:
            print("Failed to log data.")





   def check_teams_presence(self, mri):
      """
      Checks the presence of a user, using the teams.microsoft.com endpoint

      Args:
         mri (str): MRI of the user that should be checked

      Returns:
         Presence data structure (dict): Structure containing presence information about the targeted user
      """
      headers = {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + self.bearertoken,
      }

      payload = [{"mri":mri}]

      content = requests.post("https://presence.teams.microsoft.com/v1/presence/getpresence/", headers=headers, json=payload)

      if content.status_code != 200:
         p_warn("Error: %d" % (content.status_code))
         return

      json_content = json.loads(content.text)
      print(json_content)

      return json_content

   def check_live_presence(self, mri):
      """
      Checks the presence of a user, using the live.com endpoint

      Args:
         mri (str): MRI of the user that should be checked

      Returns:
         Presence data structure (dict): Structure containing presence information about the targeted user
      """
      headers = {
         "Content-Type": "application/json",
         "X-Ms-Client-Consumer-Type": "teams4life",
         "X-Skypetoken": self.skypetoken
      }

      payload = [{"mri":mri}]

      content = requests.post("https://presence.teams.live.com/v1/presence/getpresence/", headers=headers, json=payload)

      if content.status_code != 200:
         p_warn("Error: %d" % (content.status_code))
         return

      json_content = json.loads(content.text)
      return json_content
