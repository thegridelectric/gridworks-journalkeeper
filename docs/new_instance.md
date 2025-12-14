# Setting Up a New JournalDB Instance

This guide will walk you through setting up a new JournalDB instance on Ubuntu, including PostgreSQL installation, user setup, and database configuration.

## 1. Create and Configure the Ubuntu Instance

### 1.1 Create the Instance
1. Log into your Hetzner or AWS account
2. Create a new Ubuntu instance
3. Note down the IP address of your new instance

### 1.2 Initial Server Setup
1. Connect to your instance:
   ```bash
   ssh root@<ip_address>
   ```

2. Update the hostname:
   ```bash
   sudo nano /etc/hostname
   ```
   Replace the current name with `journaldb`

## 2. Install PostgreSQL

1. Update system packages and install PostgreSQL:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install postgresql
   ```

2. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```
   You should see "active (running)" in the output.

## 3. Create a Dedicated User Account

It's a security best practice to create a dedicated user account rather than using root.

1. Create a new user:
   ```bash
   adduser ubuntu
   ```
   - Enter a password when prompted
   - Skip the additional user information by pressing Enter

2. Grant sudo privileges:
   ```bash
   usermod -aG sudo ubuntu
   ```

3. Set up SSH access for the new user:
   ```bash
   mkdir -p /home/ubuntu/.ssh
   cp /root/.ssh/authorized_keys /home/ubuntu/.ssh/
   chown -R ubuntu:ubuntu /home/ubuntu/.ssh
   chmod 700 /home/ubuntu/.ssh
   chmod 600 /home/ubuntu/.ssh/authorized_keys
   ```

4. Test the new user access:
   ```bash
   ssh ubuntu@<ip_address>
   ```

## 4. Set Up the JournalDB Database

1. Access PostgreSQL as the postgres user:
   ```bash
   sudo -u postgres psql
   ```

2. Create the database and user (replace `<password>` with a strong password):
   ```sql
   CREATE USER journaldb WITH PASSWORD '<password>';
   CREATE DATABASE journaldb OWNER journaldb;
   ```

3. Exit PostgreSQL:
   ```sql
   \q
   ```

## 5. Install and Configure JournalDB

1. Install Python virtual environment support:
   ```bash
   sudo apt install python3.12-venv
   ```

2. Clone the repository:
   ```bash
   git clone git@github.com:thegridelectric/gridworks-journalkeeper.git
   cd gridworks-journalkeeper
   ```

3. Set up the Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install alembic sqlalchemy psycopg2-binary pendulum dotenv
   ```

4. Configure the database connection:
   - Create or edit `.env` file in the project directory
   - Add the following line (replace `<password>` with the database password):
     ```
     GJK_DB_URL = "postgresql://journaldb:<password>@localhost/journaldb"
     ```

5. Run database migrations:
   ```bash
   export PYTHONPATH=./src
   alembic upgrade head
   ```

## 6. Configure External Database Access

1. Allow PostgreSQL to accept external connections:
   ```bash
   sudo nano /etc/postgresql/16/main/postgresql.conf
   ```
   Add or modify the line:
   ```
   listen_addresses = '*'
   ```

2. Configure client authentication:
   ```bash
   sudo nano /etc/postgresql/16/main/pg_hba.conf
   ```
   Add the following line:
   ```
   host    journaldb    journaldb    0.0.0.0/0    md5
   ```

3. Restart PostgreSQL to apply changes:
   ```bash
   sudo systemctl restart postgresql
   ```

## Verification

To verify your setup:
1. Try connecting to the database from your local machine:
   ```bash
   psql postgresql://journaldb:<password>@<server_ip>/journaldb
   ```
2. Check that you can access the database and run queries
