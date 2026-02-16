#!/usr/bin/env python3
import smtplib
import ssl
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_creds():
    creds_file = os.path.expanduser('~/.config/fastmail/creds')
    if not os.path.exists(creds_file):
        print(f"❌ Credentials not found at {creds_file}", file=sys.stderr)
        print("Run: mkdir -p ~/.config/fastmail && echo 'YOUR_EMAIL:APP_PASSWORD' > ~/.config/fastmail/creds && chmod 600 ~/.config/fastmail/creds", file=sys.stderr)
        sys.exit(1)
    with open(creds_file) as f:
        line = f.read().strip()
        email, password = line.split(':', 1)
        return email, password

def send_mail(to, subject, body, html=False):
    email, password = load_creds()
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = email
    msg['To'] = to
    
    content_type = 'html' if html else 'plain'
    msg.attach(MIMEText(body, content_type))
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.fastmail.com', 465, context=context) as server:
        server.login(email, password)
        server.sendmail(email, to, msg.as_string())
    
    print(f"✅ Sent to {to}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--to', required=True)
    parser.add_argument('--subject', required=True)
    parser.add_argument('--body', required=True)
    parser.add_argument('--html', action='store_true')
    args = parser.parse_args()
    send_mail(args.to, args.subject, args.body, args.html)
