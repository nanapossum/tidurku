"""Konstanta domain analisis tidur."""

# R-01: acuan durasi tidur sehat untuk orang dewasa.
R01_MIN_SLEEP_HOURS = 7
R01_MAX_SLEEP_HOURS = 9

# R-02: deviasi jam tidur lebih dari 90 menit tidak konsisten.
R02_INCONSISTENCY_MINUTES = 90

# Skor konsistensi penuh diberikan hingga deviasi 30 menit.
CONSISTENCY_FULL_SCORE_MINUTES = 30
CONSISTENCY_SCORE_AT_INCONSISTENCY_LIMIT = 50
CONSISTENCY_SCORE_AFTER_INCONSISTENCY_LIMIT = 25

DURATION_SCORE_PENALTY_PER_HOUR = 20

# R-03: tidur kurang dari 6 jam selama 3 hari beruntun hingga tanggal data terakhir.
# Hari tanpa data memutus rangkaian.
R03_SHORT_SLEEP_MINUTES = 6 * 60
R03_CONSECUTIVE_SHORT_DAYS = 3

# R-04: utang dijumlahkan pada 7 hari lokal sampai as_of_date; hari tanpa data diabaikan.
R04_SLEEP_DEBT_WINDOW_DAYS = 7

# Asumsi pola begadang: jam tidur 00:00–04:59 dihitung pada tanggal tidur lokal
# dalam jendela 7 hari yang berakhir pada tanggal lokal saat analisis.
LATE_NIGHT_START_MINUTE = 0
LATE_NIGHT_END_MINUTE = 5 * 60
LATE_NIGHT_WINDOW_DAYS = 7
LATE_NIGHT_MIN_DAYS = 3

BASELINE_WINDOW_DAYS = 7
MIN_SESSIONS_FOR_PATTERNS = 3
MAX_CIRCULAR_DEVIATION_MINUTES = 12 * 60

DURATION_SCORE_WEIGHT = 0.40
CONSISTENCY_SCORE_WEIGHT = 0.35
QUALITY_SCORE_WEIGHT = 0.25
