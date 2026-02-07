import time
import logging
import random
import os
import socket

# Syslog configuration
SYSLOG_HOST = "localhost"
SYSLOG_PORT = 514

def send_syslog(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # CEF/Syslog format
    priority = "<13>" # user.notice
    syslog_msg = f"{priority}{message}"
    try:
        sock.sendto(syslog_msg.encode('utf-8'), (SYSLOG_HOST, SYSLOG_PORT))
        print(f"Sent: {message}")
    except Exception as e:
        print(f"Error sending syslog: {e}")
    finally:
        sock.close()

def generate_failed_login():
    users = ["admin", "root", "jdoe", "testuser"]
    src_ips = ["192.168.1.50", "10.0.0.5", "203.0.113.10"]
    user = random.choice(users)
    ip = random.choice(src_ips)
    msg = f"Failed password for {user} from {ip} port {random.randint(10000, 60000)} ssh2"
    send_syslog(msg)

def generate_suspicious_access():
    files = ["/etc/shadow", "/etc/passwd", "/var/www/html/config.php"]
    file = random.choice(files)
    msg = f"Suspicious access detected: attempt to read restricted file {file}"
    send_syslog(msg)

def main():
    print(f"Sending events to udp://{SYSLOG_HOST}:{SYSLOG_PORT}...")
    for _ in range(20):
        action = random.choice([generate_failed_login, generate_suspicious_access])
        action()
        time.sleep(1)

if __name__ == "__main__":
    main()
