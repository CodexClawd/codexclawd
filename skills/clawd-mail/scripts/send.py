#!/usr/bin/env python3
"""Clawd:Mail - Internal email dispatcher for OpenClaw mesh"""
import smtplib
import ssl
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.policy import SMTP

CREDS_PATH = os.path.expanduser('~/.config/fastmail/creds')

def load_creds():
    if not os.path.exists(CREDS_PATH):
        print(f"❌ Credentials not found at {CREDS_PATH}", file=sys.stderr)
        print("Setup: mkdir -p ~/.config/fastmail && echo 'email:password' > ~/.config/fastmail/creds && chmod 600 ~/.config/fastmail/creds", file=sys.stderr)
        sys.exit(1)
    with open(CREDS_PATH) as f:
        line = f.read().strip()
        email, password = line.split(':', 1)
        return email, password

def send_mail(to, subject, body, html=False, cc=None):
    email, password = load_creds()
    
    msg = MIMEMultipart('alternative', policy=SMTP)
    msg['Subject'] = subject
    msg['From'] = email
    msg['To'] = to
    
    # Add CC if provided
    recipients = [to]
    if cc:
        msg['Cc'] = cc
        recipients.append(cc)
    
    content_type = 'html' if html else 'plain'
    msg.attach(MIMEText(body, content_type))
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.fastmail.com', 465, context=context) as server:
        server.login(email, password)
        server.sendmail(email, recipients, msg.as_string())
    
    print(f"✅ Sent to {to}" + (f" (CC: {cc})" if cc else ""))
    return True

def cli():
    import argparse
    parser = argparse.ArgumentParser(description='Clawd:Mail - Send emails via Fastmail')
    parser.add_argument('--to', required=True, help='Recipient email')
    parser.add_argument('--subject', '-s', required=True, help='Email subject')
    parser.add_argument('--body', '-b', required=True, help='Email body')
    parser.add_argument('--html', action='store_true', help='Send as HTML')
    parser.add_argument('--cc', default='flo.schoedl@gmail.com', help='CC recipient (default: flo.schoedl@gmail.com)')
    args = parser.parse_args()
    send_mail(args.to, args.subject, args.body, args.html, cc=args.cc)

if __name__ == '__main__':
    cli()
