# tidurku (TidurKu)

Layanan mikro pola tidur (II3160 TST x II3140 PWAM).

## Menjalankan
    cp .env.example .env      # lalu isi JWT_SECRET
    docker compose up -d --build
    curl http://localhost:8080/api/health

Dokumentasi interaktif: `/api/docs`.
