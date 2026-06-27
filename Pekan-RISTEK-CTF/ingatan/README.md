# Ingatan

by Karev

---

## Flag

```
NETSOS{intro_to_vol4tility_4nd_mem_analysis_gampan9_lah_ya_seman9at_ngerjain_soal-soal_lain_semoga_juara}
```

## Description
Saya ketemu cara rahasia untuk masuk Netsos, tapi sayangnya tiba-tiba file saya ke encrypt semua :(

Note : Beware of malware, do not run any executable on your machine if you dont know what it does. Use a VM to be safe. 

Link: https://drive.google.com/drive/folders/14tYX3GOFK9BOKv6HmJbyydoJvsQlOIBa?usp=sharing </br>
Password : gudAtiCHtKuj3iDXGhCM7sP7hNb7rn </br>
Sha256hash dumpnya : b40ab4da18fec5361cc28bfc2f9cfbf1fe7842e28f61bbb18ff54d5509742407


Category: Forensics <br />

## Difficulty
easy-medium

## Hints
* hint 1
* hint 2
* hint dst.

## Tags
Memory analysis, volatility

## Deployment
Penjelasan cara menjalankan service yang dibutuhkan serta requirementsnya.

#### Contoh 1
- Install docker engine>=19.03.12 and docker-compose>=1.26.2.
- Run the container using:
    ```
    docker-compose up --build --detach
    ```

#### Contoh 2
- How to compile:
    ```
    gcc soal.c -o soal -O2 -D\_FORTIFY\_SOURCE=2 -fstack-protector-all -Wl,-z,now,-z,relro -Wall -no-pie
    ```
- Jalankan:
    ```
    ./soal
    ```
- Workdir di `/home/...`
- Gunakan libc 2.31 ketika sudah keluar. Alias Ubuntu 20.04.

## Notes
Tambahan informasi untuk soal, deployment, atau serangan yang mungkin terjadi pada service soal
