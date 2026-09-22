import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode('ascii')
req = urllib.request.Request('http://127.0.0.1:8000/login/admin', data=data)
try:
    resp = opener.open(req)
    print('URL after login:', resp.geturl())
    html = resp.read().decode('utf-8')
    if 'Total:' in html:
        print('Dashboard loaded successfully!')
    elif 'Secure Banking Account Management' in html:
        print('Redirected to login page!')
    else:
        print('Something else loaded.')
except Exception as e:
    print('Error:', e)
