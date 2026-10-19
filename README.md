# KMZ Photo Sorter

Otomatis menggabungkan placemark dari beberapa file `.kmz`, lalu memisahkannya menjadi dua file:

- `KMZ_SUDAH_BERISI_FOTO.kmz`: lokasi dengan foto lokal yang berhasil ditemukan.
- `KMZ_BELUM_ADA_FOTO.kmz`: lokasi yang tidak memiliki foto yang terdeteksi.
- `LAPORAN_PEMROSESAN.txt`: ringkasan pemrosesan.

## Fitur

- Memproses semua file KMZ di folder input.
- Menggabungkan placemark dari berbagai KMZ.
- Menyalin foto yang direferensikan dari dalam arsip KMZ dan memperbarui referensinya.
- Opsional mencocokkan nama dan koordinat terhadap daftar target CSV.
- Menggunakan pustaka standar Python, tanpa dependensi pihak ketiga.

## Persyaratan

- Python 3.10 atau lebih baru direkomendasikan.
- Windows, macOS, atau Linux untuk menjalankan skrip Python. Peluncur `.bat` disediakan untuk Windows.

## Cara menjalankan

```bash
python kmz_photo_sorter.py /path/ke/kmz-input /path/ke/hasil
```

Contoh Windows:

```powershell
python kmz_photo_sorter.py "C:\KMZ\Input" "C:\KMZ\Output"
```

Untuk mencocokkan hanya titik yang tercantum dalam CSV:

```bash
python kmz_photo_sorter.py FOLDER_INPUT FOLDER_OUTPUT targets.csv
```

CSV harus memiliki kolom nama, lintang, dan bujur. Nama kolom yang dikenali antara lain `name`/`nama`, `latitude`/`lat`, dan `longitude`/`langitude`/`lon`/`lng`.

Di Windows, kamu juga dapat menjalankan `JALANKAN_KMZ_OTOMATIS.bat` dan memasukkan folder input serta output saat diminta.

## Catatan tentang deteksi foto

Skrip menandai foto jika placemark merujuk ke file gambar lokal di arsip KMZ atau memiliki gambar base64 pada deskripsinya. Foto yang hanya ditautkan dari web, atau yang disimpan melalui struktur KML khusus, mungkin tidak terdeteksi. Selalu verifikasi hasil di Google Earth Pro sebelum dipakai sebagai data final.

Simpan file sumber sebagai salinan cadangan. Skrip tidak mengubah file input.

## Struktur proyek

```text
kmz-photo-sorter/
├── kmz_photo_sorter.py
├── JALANKAN_KMZ_OTOMATIS.bat
├── PETUNJUK_KMZ_OTOMATIS.txt
├── README.md
├── LICENSE
└── .gitignore
```

## Lisensi

MIT. Lihat `LICENSE`.
