#!/bin/bash

# Değişkenler
APP_NAME="kuran-tefsir"
VERSION="1.0"
BUILD_DIR="build_pkg"
OPT_DIR="$BUILD_DIR/opt/$APP_NAME"
BIN_DIR="$BUILD_DIR/usr/bin"
APP_DIR="$BUILD_DIR/usr/share/applications"

echo "--- Debian Paketi Hazırlama Başladı ---"

# 1. Temizlik
rm -rf $BUILD_DIR
mkdir -p $DEBIAN_DIR $OPT_DIR $BIN_DIR $APP_DIR

# 2. Uygulama Dosyasını Kopyala
if [ -f "kuranoku.py" ]; then
    cp kuranoku.py $OPT_DIR/main.py
    chmod +x $OPT_DIR/main.py
else
    echo "HATA: kuranoku.py dosyası bulunamadı!"
    exit 1
fi

# 3. Başlatıcı Betiği Oluştur (/usr/bin/kuran-uygulamasi)
cat <<EOF > $BIN_DIR/$APP_NAME
#!/bin/bash
cd /opt/$APP_NAME
python3 main.py "\$@"
EOF
chmod +x $BIN_DIR/$APP_NAME

# 4. Masaüstü Kısayolu Oluştur (.desktop)
cat <<EOF > $APP_DIR/$APP_NAME.desktop
[Desktop Entry]
Name=Kur'an-ı Kerim Tefsir
Comment=Diyanet Meali ve Tefsiri (Çevrimdışı)
Exec=$APP_NAME
Icon=help-about-symbolic
Terminal=false
Type=Application
Categories=Education;Religion;
EOF

# 5. Debian Kontrol Dosyası Oluştur
mkdir -p $BUILD_DIR/DEBIAN
cat <<EOF > $BUILD_DIR/DEBIAN/control
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: MT
Depends: python3, python3-requests, python3-gi, libadwaita-1-0, gir1.2-adw-1, fonts-hosny-amiri
Description: Diyanet Meali ve Tefsiri iceren Kuran uygulamasi.
 /opt dizinine kurulur ve SQLite veritabanini orada saklar.
EOF

# 6. Paketleme Yap
dpkg-deb --build $BUILD_DIR ${APP_NAME}_${VERSION}.deb

echo "--- İşlem Tamamlandı ---"
echo "Oluşturulan paket: ${APP_NAME}_${VERSION}.deb"
echo "Kurmak için: sudo apt install ./${APP_NAME}_${VERSION}.deb"