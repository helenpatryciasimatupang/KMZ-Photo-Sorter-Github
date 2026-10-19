@echo off
setlocal
 title Otomatis Gabung KMZ berdasarkan Foto
 echo.
 echo === OTOMATIS GABUNG DAN PISAHKAN KMZ ===
 echo Simpan semua pecahan KMZ dalam satu folder terlebih dahulu.
 echo.
 set /p INPUT=Masukkan alamat folder input KMZ: 
 set /p OUTPUT=Masukkan alamat folder output: 
 python "%~dp0kmz_photo_sorter.py" "%INPUT%" "%OUTPUT%"
 echo.
 pause
