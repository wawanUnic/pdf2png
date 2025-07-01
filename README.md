# pdf2png (web)

## Hard:
- Processor / Memory: Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz (4 cores) / 32GB DDR4 2133 MHz
- OS / Platform: Ubuntu 24.04.2 LTS / x86_64
- Storage: SSD 120GB

## Ports used (server):
- 22 - SSH - server management. Login only by key
- 7654 - HTTP - pdf2png-portal

## Add a new user
Working as root

User name:password
```
adduser name
usermod -aG sudo name
su - name
sudo ls -la /root
sudo reboot
```

## Create keys for SSH
Working as root

```
ssh-keygen
cd .ssh
ls -l
nano id_rsa
mv id_rsa.pub authorized_keys
chmod 644 authorized_keys
```
Copy the contents of the private key from the console and save it in an empty format on your PC using a text editor.
The file name is not critical. Important: the private key must contain:
```
-----START OPENSH PRIVATE KEY-----
...
-----END OPENSSH ПРИВАТНЫЙ КЛЮЧ-----
```
Copy the public key to all users in the .ssh folder.
You need to set 644 rights for all users.
In Windows, load PuTTYgen. In the menu: click Conversions->Import key and find the saved private key file.
It will load into the program. Click "Save private key" in PuTTY .ppk format in D:\Program Files\PuTTY\KEYs.
Load the .ppk file into your SSH profile in the PuTTY program: Connection->SSH->Auth->Credentials
Connection - keepAlive 15 sec
Saving your profile in PuTTY

## We prohibit login by password
We work as root

nano /etc/ssh/sshd_config:
```
PubkeyAuthentication yes
PasswordAuthentication no
```
service ssh restart

## We will update the system
We work from name
```
sudo apt update
sudo apt upgrade
sudo reboot
sudo apt-get install python3-pip
sudo apt install python3.12-venv
sudo apt install poppler-utils
```

## Copying source files
Working from name

Create a pdf2png folder. Copy the source files into it.

Give execution rights (!!! Give the /home/name folder rights to R+X other, with the chmod o+rX /home/name command):
```
find pdf2png/ -type f -exec chmod 755 {} \;
```

## Create a virtual environment
Working from name

Versions of added packages:
```
annotated-types   0.7.0
anyio             4.9.0
click             8.2.1
fastapi           0.115.14
h11               0.16.0
idna              3.10
pdf2image         1.17.0
pillow            11.2.1
pip               24.0
pydantic          2.11.7
pydantic_core     2.33.2
python-multipart  0.0.20
sniffio           1.3.1
starlette         0.46.2
typing_extensions 4.14.0
typing-inspection 0.4.1
uvicorn           0.35.0
```

```
cd /home/name/pdf2png
python3 -m venv myenv
source myenv/bin/activate
pip install fastapi uvicorn pdf2image pillow python-multipart
pip list
uvicorn app:app --reload --host 0.0.0.0 --port 7654 -- Do not run this command! This is for manual testing only.
```

## Adding services to systemD
Working from name

For a simple test it is enough - uvicorn app:app --reload --host 0.0.0.0 --port 7654

sudo nano /etc/systemd/system/pdf2png.service (python3.12?):
```
[Unit]
Description=pdf2png
After=network-online.target nss-user-lookup.target

[Service]
User=name
Group=name
WorkingDirectory=/home/name/pdf2png
Environment="PYTHONPATH=/home/name/pdf2png/myenv/lib/python3.12/site-packages"
ExecStartPre=/usr/bin/sleep 10
ExecStart=/home/name/pdf2png/myenv/bin/python3.12 /home/name/pdf2png/app.py
??? ExecStart=/home/name/pdf2png/uvicorn app:app --reload --host 0.0.0.0 --port 7654 ???

RestartSec=10
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Configure systemD:
```
sudo systemctl daemon-reload
sudo systemctl enable --now pdf2png.service
systemctl status pdf2png.service
```
