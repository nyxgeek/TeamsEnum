#!/usr/bin/python3

from datetime import datetime
import sys
import json
import os
from colorama import Fore, Style
import errno
import re
import hashlib
from html import unescape
import mysql.connector
from mysql.connector import Error
import configparser

def p_err(msg, exit=False, exitcode=1, end="\n"):
   """
   Prints a string, highlighted in red.

   Args:
       msg (str): The message to be printed.
       exit (boolean): If True, exits after printing the message
       exitcode (int): If exit is True, exit program using this exit code
       end (str): Line terminator after printing. Defaults to newline

   Returns:
       None
   """
   print(Fore.RED + "[-] ", end='')
   p_normal(msg, exit, exitcode, end)

def p_warn(msg, exit=False, exitcode=1, end="\n"):
   """
   Prints a string, highlighted in yellow.

   Args:
       msg (str): The message to be printed.
       exit (boolean): If True, exits after printing the message
       exitcode (int): If exit is True, exit program using this exit code
       end (str): Line terminator after printing. Defaults to newline

   Returns:
       None
   """
   print(Fore.YELLOW + "[-] ", end='')
   p_normal(msg, exit, exitcode, end)

def p_success(msg, exit=False, exitcode=0, end="\n"):
   """
   Prints a string, highlighted in green.

   Args:
       msg (str): The message to be printed.
       exit (boolean): If True, exits after printing the message
       exitcode (int): If exit is True, exit program using this exit code
       end (str): Line terminator after printing. Defaults to newline

   Returns:
       None
   """
   print(Fore.GREEN + "[+] ", end='')
   p_normal(msg, exit, exitcode, end)

def p_info(msg, exit=False, exitcode=0, end="\n"):
   """
   Prints a string, highlighted in cyan.

   Args:
       msg (str): The message to be printed.
       exit (boolean): If True, exits after printing the message
       exitcode (int): If exit is True, exit program using this exit code
       end (str): Line terminator after printing. Defaults to newline

   Returns:
       None
   """
   print(Fore.CYAN + "[~] ", end='')
   p_normal(msg, exit, exitcode, end)

def p_normal(msg, exit=False, exitcode=0, end="\n"):
   """
   Prints a string.

   Args:
       msg (str): The message to be printed.
       exit (boolean): If True, exits after printing the message
       exitcode (int): If exit is True, exit program using this exit code
       end (str): Line terminator after printing. Defaults to newline

   Returns:
       None
   """
   print(msg, end='')
   print(Style.RESET_ALL, end=end)
   if exit:
      sys.exit(exitcode)

def p_file(msg, fd=None):
   """
   Writes a message to the provided file descriptor

   Args:
       msg (str): The message to be written into a file.
       fd (_io.TextIOWrapper): File descriptor used for file write

   Returns:
       None
   """
   if fd is None:
      return
   fd.write(msg)
   fd.write("\n")
   fd.flush()

def open_file(filename):
   """
   Prints a string.

   Args:
       filename (str): Name of the file that is used for logging the results

   Returns:
       File descriptor (_io.TextIOWrapper): File descriptor that is later used for write operations
   """
   try:
      os.stat(filename)
      overwrite = ""
      while overwrite not in ["y","n"]:
         p_warn("The output file already exists. Overwrite? (y/n): ", end='')
         overwrite = input()
      if overwrite == "n":
         p_warn("Output file will not be overwritten. Please choose another file", True, 1)

   except FileNotFoundError as err:
      pass

   try:
      fd = open(filename, 'w')
   except IOError as err:
      if err.errno == errno.EACCES:
         p_warn("No permissions to write output file", True, 1)
      elif err.errno == errno.EISDIR:
         p_warn("Output file is a directory", True, 1)

   return fd

def check_db_conf(file_path="db.conf"):
    """
    Checks the database configuration file and returns the configuration values.

    Args:
        file_path (str): Path to the database configuration file.

    Returns:
        dict: A dictionary containing database configuration values if valid.
        None: If the configuration is invalid or the file is missing.
    """
    # Check if db.conf exists
    if not os.path.isfile(file_path):
        print(f"Error: Configuration file '{file_path}' does not exist.")
        return None

    # Parse db.conf
    config = configparser.ConfigParser()
    config.read(file_path)

    if 'mysql' not in config:
        print(f"Error: Section [mysql] not found in '{file_path}'.")
        return None

    # Get connection info
    try:
        db_config = {
            "host": config['mysql']['host'],
            "user": config['mysql']['user'],
            "password": config['mysql']['password'],
            "database": config['mysql']['database'],
            "presence_table": config['mysql']['presence_table'],
            "ooo_table": config['mysql']['ooo_table'],
            "user_info_table": config['mysql']['user_info_table']
        }
        return db_config
    except KeyError as e:
        print(f"Error: Missing key {e} in '{file_path}'.")
        return None

def log_ooo_db(db_config, teams_guid, raw_message):
    """
    Logs the OOO message to the database if it's unique.
    """
    try:
        # Calculate MD5 hash and sanitize/truncate the message
        md5sum = calculate_md5(raw_message)
        sanitized_text, truncated = sanitize_and_truncate(raw_message)
        message_length = len(raw_message)

        print(f"MD5: {md5sum}, Length: {message_length}, Truncated: {truncated}")

        # Current timestamp details
        now = datetime.now()
        current_date = now.strftime('%Y-%m-%d')
        current_time = now.strftime('%H:%M:%S')
        unix_timestamp = int(now.timestamp())

        connection = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )

        if connection.is_connected():
            cursor = connection.cursor()

        ooo_table=db_config["ooo_table"]
        # SQL query to insert the OOO message
        query = f"""
            INSERT IGNORE INTO {ooo_table} (
                md5sum, teams_guid, scrape_date, scrape_time, scrape_date_unix, length, truncated, text
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (md5sum, teams_guid, current_date, current_time, unix_timestamp, message_length, int(truncated), sanitized_text)

        # Execute the query
        cursor.execute(query, values)
        connection.commit()
        print("OOO message logged successfully.")
        return True
    except Error as e:
        print(f"Failed to log presence data: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()



def log_userinfo_db(db_config, content_text):
    """
    Parses content_text, extracts user information, and logs it to the database.
    """
    try:
        # Split the content into separate JSON-like parts
        content_parts = content_text.split("\n")
        if len(content_parts) < 1:
            raise ValueError("Invalid format: Expected at least one JSON object.")

        # Parse the first part as the user information
        user_info = json.loads(content_parts[0].strip())  # Ensure it's parsed as JSON

        # Parse the second part as presence information (optional)
        presence_info = None
        if len(content_parts) > 1:
            try:
                presence_info = json.loads(content_parts[1].strip())
            except json.JSONDecodeError:
                print("Second part is not valid JSON, skipping presence information.")

        # Prepare database connection
        now = datetime.now()
        current_date = now.strftime('%Y-%m-%d')
        current_time = now.strftime('%H:%M:%S')
        unix_timestamp = int(now.timestamp())

        connection = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )

        if connection.is_connected():
            cursor = connection.cursor()

        # Process each user in the user_info list
        for user in user_info:
            object_id = user.get("objectId")
            user_principal_name = user.get("userPrincipalName")

            # Essential fields must be present
            if not object_id or not user_principal_name:
                print(f"Skipping entry. Missing essential fields: {user}")
                continue

            # Non-essential fields
            email = user.get("email", None)
            display_name = user.get("displayName", None)
            tenant_id = user.get("tenantId", None)
            co_existence_mode = user.get("featureSettings", {}).get("coExistenceMode", None)
            given_name = user.get("givenName", None)
            surname = user.get("surname", None)
            account_enabled = user.get("accountEnabled", None)
            tenant_name = user.get("tenantName", None)
            country = user.get("Country", None)
            city = user.get("City", None)


            # SQL query to insert the user info with INSERT IGNORE
            query = """
                INSERT IGNORE INTO user_info_all (
                    object_id, user_principal_name, email, display_name, tenant_id,
                    co_existence_mode, given_name, surname, account_enabled, tenant_name,
                    country, city, scrape_date, scrape_time, scrape_date_unix
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                object_id, user_principal_name, email, display_name, tenant_id,
                co_existence_mode, given_name, surname, account_enabled, tenant_name,
                country, city, current_date, current_time, unix_timestamp
            )

            # Execute the query
            cursor.execute(query, values)

        connection.commit()
        print("User information logged successfully.")
        return True

    except Error as e:
        print(f"Failed to log user information: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return False
    except ValueError as e:
        print(f"Invalid format: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def log_presence_db(db_config, teams_guid, availability, ooo_enabled, device, scrape_date_unix, scrape_date, hh_period, qh_period, session):
    """
    Logs user presence data into the MySQL database.

    Args:
        db_config (dict): A dictionary containing database configuration values.
        teams_guid (str): GUID of the user.
        availability (str): User status (e.g., 'away', 'busy').
        ooo_enabled (bool): Out of office status (True = 1, False = 0).
        device (str): Device type (e.g., 'desktop', 'mobile').
        scrape_date_unix (int): Timestamp in UNIX time.
        scrape_date (str): Date in YYYY-MM-DD format.
        hh_period (int): Half-hour period (0-47).
        qh_period (int): Quarter-hour period (0-95).

    Returns:
        bool: True if the data is logged successfully, False otherwise.
    """
    try:
        connection = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )


        if connection.is_connected():
            cursor = connection.cursor()

            presence_table=db_config["presence_table"]

            # SQL query to insert presence data
            query = f"""
                INSERT INTO {presence_table} (
                    teams_guid,
                    availability,
                    ooo_enabled,
                    device,
                    scrape_date_unix,
                    scrape_date,
                    hh_period,
                    qh_period,
                    session
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Execute query with provided values
            cursor.execute(query, (
                teams_guid,
                availability,
                int(ooo_enabled),  # Convert bool to int
                device,
                scrape_date_unix,
                scrape_date,
                hh_period,
                qh_period,
                session
            ))
            connection.commit()
            print("Presence data logged successfully.")
            return True
    except Error as e:
        print(f"Failed to log presence data: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def remove_html_preserve_newlines(text):
    """Removes HTML tags from text while preserving newlines."""
    # Unescape HTML entities first
    text = unescape(text)
    # Replace <br>, <p>, and similar tags with newlines
    text = re.sub(r'<\s*(br|p|div)\s*/?>', '\n', text, flags=re.IGNORECASE)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize multiple newlines
    text = re.sub(r'\n+', '\n', text).strip()
    return text

def sanitize_and_truncate(text, max_length=1000):
    # Remove non-alphanumeric characters except spaces and basic punctuation
    allowed_pattern = r"[^a-zA-Z0-9\s.,!?@#&'\"()-:åÅøØæÆ]"
    sanitized = re.sub(allowed_pattern, "", text)
    #sanitized = re.sub(r"[^a-zA-Z0-9\s.,!?@#&'\"()-:]", "", text)
    # Truncate the sanitized text
    truncated = len(sanitized) > max_length
    sanitized = sanitized[:max_length]
    return sanitized, truncated

def calculate_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()
