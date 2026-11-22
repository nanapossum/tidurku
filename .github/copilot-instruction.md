# TidurKu: konteks untuk Copilot
Layanan mikro pola tidur (tugas kuliah, data uji saja, bukan saran medis). Satu proses FastAPI di Docker ARM64 (RAM <= 256 MB), di belakang Nginx (prefix /api), SQLite di /data.
Stack: FastAPI, SQLAlchemy 2.0, pydantic v2, pyjwt, bcrypt, httpx, pytest. Dilarang menambah dependensi berat (tanpa pandas/numpy, Redis, ORM lain).

## Struktur
core-service/app/<konteks>/ : identity, tracking, goals, analysis, reminders, environment, public. Satu modul per bounded context. Antar-konteks hanya lewat fungsi service/repository publik atau events.py, jangan impor model konteks lain (kecuali FK ke users).

## Konvensi API
- Semua rute di bawah /api, satu router per konteks, di-include di main.py.
- JSON camelCase (pydantic alias_generator=to_camel, populate_by_name=True, response by_alias). Kolom DB snake_case.
- ID = UUID4 string. Waktu: terima ISO 8601 beroffset, simpan UTC, kembalikan UTC berakhiran "Z". Tanggal kalender dan jam tidur dihitung di zona Asia/Jakarta (setting TIMEZONE).
- Error seragam: {"code":"UPPER_SNAKE","detail":"pesan bahasa Indonesia"}. 401 token/API key tidak valid, 404 tidak ada (termasuk milik user lain), 409 konflik, 422 validasi. Tanpa stack trace ke klien.
- Setiap query data pribadi wajib difilter user_id; data user lain tidak boleh bocor, termasuk lewat pesan error.

## Keamanan
JWT_SECRET wajib dari env (tanpa default), min 32 karakter. bcrypt untuk password. Bandingkan secret/API key dengan secrets.compare_digest. Jangan log password, token, atau API key.

## Aturan domain
R-01 durasi ideal dewasa 7-9 jam. R-02 deviasi jam tidur >90 menit dari rata-rata = tidak konsisten. R-03 tiga hari berturut-turut <6 jam = peringatan utang tidur. R-04 utang tidur = akumulasi max(0, target - aktual) 7 hari terakhir. R-05 sesi satu user tidak boleh tumpang tindih. R-06 kualitas 1-5. R-07 rekomendasi bertahap, geser maks 30 menit per langkah. R-08 agregat hanya bila >= 5 pengguna.
Skor sesi 0-100 tidak disimpan, selalu dihitung ulang dari data sumber.

## Pengujian
pytest di core-service/tests, TestClient + SQLite in-memory (override get_db), tanpa akses jaringan (mock httpx). Tiap paket wajib punya test jalur sukses dan setiap aturan/validasi, termasuk nilai batas.

## Aturan kerja
Kerjakan hanya paket yang diminta, jangan ubah file di luar daftar. Python 3.12, type hints, logika domain berupa fungsi murni terpisah dari FastAPI, komentar singkat bahasa Indonesia. Jalankan pytest sampai hijau. Di akhir tulis: file yang dibuat/diubah, asumsi yang kamu ambil, perbedaan dengan kode di mobile/, dan hal yang tidak bisa kamu uji.