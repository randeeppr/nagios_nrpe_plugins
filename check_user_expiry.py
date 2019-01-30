#!/usr/bin/python
import sys,subprocess,datetime,re,calendar,getopt

STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3

# Usage
def usage():
  print("\n")
  print("Checks the users with Account/Password expiry less than n days.")
  print("\t-h : Prints this help")
  print("\t-w : Warning threshold")
  print("\t-V : Enables verbose")
  print("Usage :./check_user_expiry.py -w 10")
  print("\n")
  sys.exit(STATUS_UNKNOWN)

def list_to_dict(rlist):
    return dict(map(lambda s : s.split(':'), rlist))

def date_to_datetime(expiry_date):
    #date_pattern = re.search(Feb 14, 2019)
    expiry_date_pattern = re.search('(\w+) (\d\d), (\d\d\d\d)',expiry_date)
    day = int(expiry_date_pattern.group(2))
    year = int(expiry_date_pattern.group(3))
    month = expiry_date_pattern.group(1)
    month_to_num = {name: num for num, name in enumerate(calendar.month_abbr) if num}
    month =  month_to_num[month]
    expiry = datetime.datetime(year=year, month=month, day=day)
    return expiry  

# Main function starts here
def main(argv):
  verbose = False
  # Getting commandline arguments
  if len(sys.argv) < 2:
    usage()
  try:
        opts, args = getopt.getopt(argv,"hw:V")
  except getopt.GetoptError:
        usage()
  for opt, arg in opts:
        if opt == '-h':
                usage()
        elif opt in ("-w", "--warning"):
                warning_threshold = int(arg)
        elif opt in ("-V", "--verbose"):
                verbose = True

  users_uid = subprocess.check_output("cut -d : -f 1,3 /etc/passwd", shell=True)
  users_uid = users_uid.split("\n")
  users_uid = filter(None,users_uid)
  users_uid = list_to_dict(users_uid)

  users_to_check = {}
  for user,uid in users_uid.items():
    if int(uid) > 500:
      users_to_check[user] = int(uid)

  user_chage = {}
  for user,uid in users_to_check.items():
      chage_op = subprocess.check_output("chage -l {0}".format(user), shell=True)
      chage_op = chage_op.split("\n")
      chage_op = filter(None,chage_op)
      chage_op = list_to_dict(chage_op)
      chage_op = dict(map(str.strip,z) for z in chage_op.items())
      user_chage[user]=chage_op
  
  #print(user_chage)
  now = datetime.datetime.now()
  users_expiring = []
  for user,details in user_chage.items():
     if details['Password expires'] != "never" and details['Account expires'] != "Never":
       password_expiry = details['Password expires']
       if verbose:
         print(password_expiry)
       password_expiry = date_to_datetime(password_expiry)
       if verbose:
         print(password_expiry)
       pass_diff = password_expiry - now
       if verbose:
         print(pass_diff.days)
       account_expiry  = details['Account expires']
       if verbose:
         print(account_expiry)
       account_expiry = date_to_datetime(account_expiry)
       if verbose:
         print(account_expiry)
       exp_diff = account_expiry - now
       if verbose:
         print(exp_diff.days)
       if (pass_diff.days < warning_threshold ) or (exp_diff.days < warning_threshold) :
         users_expiring.append(user)
       
  if verbose:
    print(users_expiring)

  if users_expiring:
    print("The following users have password/account expiry in less than {0} day(s) : {1}".format(warning_threshold,",".join(users_expiring)))
    sys.exit(2)
  else:
    print("No users with password/account expiry in less than {0} day(s) found.".format(warning_threshold))
    sys.exit(0)

if __name__ == "__main__":
   main(sys.argv[1:])
