import requests

s = requests.Session()
res = s.post('http://127.0.0.1:8000/login/admin', data={'username': 'admin', 'password': 'admin123'}, allow_redirects=False)
print('Status Code:', res.status_code)
print('Headers:', res.headers)
print('Cookies:', s.cookies.get_dict())
res2 = s.get('http://127.0.0.1:8000/', allow_redirects=False)
print('Status Code 2:', res2.status_code)
print('Headers 2:', res2.headers)
