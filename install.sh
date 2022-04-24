#!/bin/bash

#can be modified accordingly
SERVER_IP=178.128.153.108
CURRENTDIR=$(pwd)
WorkingDirectory=$(pwd)
ENV_NAME='venv'
WHOAMI=`whoami`

# 1. Install python and nginx
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y python3-pip python3-dev python3.8-venv libjpeg8-dev libpng-dev libfreetype6-dev nginx
sudo apt install git curl 

# 2. create virtual_environment
echo 'setup virtualenv'
python3 -m venv $WorkingDirectory/$ENV_NAME

# 3. Activate virtual_environment and make migrations
source $WorkingDirectory/$ENV_NAME/bin/activate
pip install -U pip
pip install -r requirements.txt
python manage.py migrate



# create socket 

sudo rm -rf /etc/systemd/system/logodetect.socket

sudo echo "
[Unit]
Description=logodetect socket

[Socket]
ListenStream=/run/logodetect.sock

[Install]
WantedBy=sockets.target " | sudo tee --append /etc/systemd/system/logodetect.socket


# 5. Create gunicorn systemd service

echo 'setup gunicorn'

sudo rm /etc/systemd/system/logodetect.service

sudo echo "

[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=$WHOAMI

Group=www-data

WorkingDirectory=$WorkingDirectory/
ExecStart=$WorkingDirectory/$ENV_NAME/bin/gunicorn --access-logfile $WorkingDirectory/log/access_file_g.log --error-logfile $WorkingDirectory/log/error_file_g.log --capture-output --enable-stdio-inheritance  --workers 1 --max-requests 1 --bind unix:/run/logodetect.sock logo_detect_api.wsgi:application

[Install]
WantedBy=multi-user.target
" | sudo tee --append /etc/systemd/system/logodetect.service



# 6. Start gunicorn service
sudo systemctl start $WHOAMI
sudo systemctl enable $WHOAMI

sudo systemctl daemon-reload
sudo systemctl restart $WHOAMI


# 7. Create Nginx template
sudo rm -rf /etc/nginx/sites-available/$WHOAMI
echo 'setup Nginx'
sudo echo "
server {
    listen 80;
    server_name $SERVER_IP;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $WorkingDirectory;
    }

    location /media/ {
        root $WorkingDirectory;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:run/logodetect.sock;
    }
}" | sudo tee --append /etc/nginx/sites-available/$WHOAMI


sudo ln -s /etc/nginx/sites-available/$WHOAMI /etc/nginx/sites-enabled

sudo nginx -t

sudo systemctl restart nginx
sudo systemctl daemon-reload