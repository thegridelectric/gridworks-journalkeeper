## JournalDB Setup


Changed /etc/postgresql/14/main/postgresql.conf:

```
listen_addresses = '*'
```

Changed /etc/postgresql/14/main/pg_hba.conf, added:
```
host    all             all             0.0.0.0/0               md5
```

Then 

```
sudo systemctl restart postgresql
```


## How to store data
