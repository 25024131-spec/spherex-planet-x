import urllib.request, re, http.cookiejar, urllib.parse

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

file_id = '12mACroJtYEWZqnkmMVfkTCB2EcQ2BK3_'
url = f'https://drive.google.com/uc?export=download&id={file_id}'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

with opener.open(req) as resp:
    data = resp.read().decode('utf-8', errors='ignore')
    forms = re.findall(r'<form.*?action=[\'"](.*?)[\'"].*?>(.*?)</form>', data, re.DOTALL)
    if forms:
        action, body = forms[0]
        inputs = dict(re.findall(r'<input.*?name=[\'"](.*?)[\'"].*?value=[\'"](.*?)[\'"]', body))
        get_url = action + '?' + urllib.parse.urlencode(inputs)
        req2 = urllib.request.Request(get_url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req2) as resp2:
            file_data = resp2.read()
            print('Downloaded bytes:', len(file_data), 'Sample:', file_data[:80])
