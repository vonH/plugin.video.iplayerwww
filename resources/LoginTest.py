import requests
import re
import cookielib

#Need entering manually
testUser = ""
testPass = ""

cookie_jar = cookielib.LWPCookieJar(filename='testCookie.txt')

#Regular expression to get 'nonce' from login page
p = re.compile('form method="post" action="([^""]*)"')

# Do a separate account check outside of session to match our non-session set-up
r = requests.head("https://www.bbc.com/account", cookies=cookie_jar, allow_redirects=False)
if r.status_code == 200:
    print "Account logged in"
else: 
    print "Not logged in"

# We need an initial session set-up with BBC (set cookies maybe)
with requests.Session() as s:
    r = s.get('https://www.bbc.com/')

    # Call the login page to get a 'nonce' for actual login
    signInUrl = 'https://www.bbc.com/session'
    r = s.get(signInUrl)
    m = p.search(r.text)
    url = m.group(1)

    post_data={
        'username': testUser,
        'password': testPass,
        'attempts':'0'}

    url = "https://www.bbc.com%s" % url
    r = s.post(url, data=post_data)
    for cookie in s.cookies:
        cookie_jar.set_cookie(cookie)
    cookie_jar.save(ignore_discard=True)
    
# Do a separate account check outside of session to match our non-session set-up
r = requests.head("https://www.bbc.com/account", cookies=cookie_jar, allow_redirects=False)
if r.status_code == 200:
    print "Account logged in"
else: 
    print "Not logged in"

# Do a separate account check outside of session to match our non-session set-up
with requests.Session() as s:
    r = s.get("https://www.bbc.com/session/signout", cookies=cookie_jar)
    if r.status_code == 200:
        print "Sign-out success"
    else: 
        print "Sign-out failed"
    
# Do a separate account check outside of session to match our non-session set-up
r = requests.head("https://www.bbc.com/account", cookies=cookie_jar, allow_redirects=False)
if r.status_code == 200:
    print "Account logged in"
else: 
    print "Not logged in"