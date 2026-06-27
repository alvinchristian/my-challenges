# Writeup Ingatan

Bikin volatility symbol table sendiri ikutin step di https://www.hackthebox.com/blog/how-to-create-linux-symbol-tables-volatility#mcetoc_1irpkuuf42n (or kalo udh ada online brti hoki wkwk)

## Soal 1 & 2

```
vol.py -f dump linux.pslist (cari Encryptor)
```

## Soal 3

dump files pake `linux.pagecache.InodePages --find /home/vboxuser/Documents/netsos --dump`

## Soal 4

Rev binary netsos

## Soal 5

dump file yg diencrypt pake `linux.pagecache.InodePages --find /home/vboxuser/Documents/rahasia.txt.enc --dump`

rename ke `rahasia.txt.enc`

tinggal jalanin decrypt.py

