# tidurku (TidurKu)

Layanan mikro pola tidur (II3160 TST x II3140 PWAM).

## Menjalankan
    cp .env.example .env      # lalu isi JWT_SECRET
    docker compose up -d --build
    curl http://localhost:8080/api/health

Dokumentasi interaktif: `/api/docs`.

## Menjalankan aplikasi mobile

Jalankan backend dengan Docker seperti langkah di atas, lalu jalankan UI:

    cd mobile
    npm install
    npx expo start

UI menggunakan API backend. Android Emulator memakai `http://10.0.2.2:8080` secara default; iOS Simulator memakai `http://localhost:8080`. Untuk ponsel fisik, salin `mobile/.env.example` menjadi `mobile/.env`, lalu ubah `EXPO_PUBLIC_API_URL` ke alamat IP lokal komputer yang menjalankan Docker, misalnya `http://192.168.1.10:8080`. Ponsel dan komputer harus berada di jaringan yang sama. Setelah mengubah alamat, mulai ulang Expo.

Akun demo lama di UI tidak lagi digunakan karena autentikasi sekarang memeriksa database backend. Buat akun lewat **Daftar**, lalu gunakan akun tersebut untuk masuk.
