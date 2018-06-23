# UPDATE PVER to actual version
# ./create_ipk_new.sh 20180510 ... [date of release]
if [ ! "`whoami`" = "root" ]
then
    echo "*************************** Please run script as root ***************************"
    exit 1
fi

echo " "
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "!!!! run command 'sudo su' then run script !!!!"
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo " "


##################################
############ SETTINGS ############
##################################
ADDONS_COMMIT="5dfe5f501a659b83695b9977dd45fbe463911a0e"
PVER="1.0"
SH4_V="0.1"
MIPS_V="0.2"
PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK


############ SCRIPT ############
D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
S=${D}/ipkg.src.$$
P=${D}/ipkg.tmp.$$
B=${D}/ipkg.build.$$
DP=${D}/ipkg.deps

P26="https://www.python.org/ftp/python/2.6/Python-2.6.tgz"
P27="https://www.python.org/ftp/python/2.7.5/Python-2.7.5.tgz"

SH4="http://dl.bintray.com/mx3l/generic/sh4_$SH4_V.tar.gz"
MIPS="http://dl.bintray.com/mx3l/generic/mipsel_$MIPS_V.tar.gz"

pushd ${D} &> /dev/null

GITVER=${1}
if [ -z "$1" ]; then
	GITVER=$(git log -1 --format="%ci" | awk -F" " '{ print $1 }' | tr -d "-")
fi
VER=$PVER-$GITVER
PKG=${D}/archivczsk_${VER}

popd &> /dev/null

rm -rf ${D}/ipkg.src*
rm -rf ${D}/ipkg.tmp*
rm -rf ${D}/ipkg.build*

mkdir -p ${P}
mkdir -p ${P}/CONTROL
mkdir -p ${B}
mkdir -p ${DP}
mkdir -p ${S}

git archive --format=tar HEAD | (cd ${S} && tar xf -)

if ! [ -z "$1" ]; then
	rm -rf ${S}/build/plugin
	cp -r ${D}/build/plugin ${S}/build/
fi


if [ -d ${DP}/Python-2.6 ] && [ -d ${DP}/Python-2.7 ]; then
	echo "python packages are already downloaded"
else
	echo "downloading neccesary python packages..."
	curl $P26 -s -o ${DP}/Python-2.6.tgz
	curl $P27 -s -o ${DP}/Python-2.7.5.tgz
	tar -C ${DP} -xzf ${DP}/Python-2.6.tgz
	tar -C ${DP} -xzf ${DP}/Python-2.7.5.tgz
	mv ${DP}/Python-2.7.5 ${DP}/Python-2.7
fi

rm -rf ${DP}/sh4
rm -rf ${DP}/mipsel

echo "downloading neccesary sh4/mipsel binaries"
curl $SH4 -L -s -o ${DP}/sh4_$SH4_V.tar.gz
curl $MIPS -L -s -o ${DP}/mipsel_$MIPS_V.tar.gz 
tar -C ${DP} -xzf ${DP}/sh4_$SH4_V.tar.gz
tar -C ${DP} -xzf ${DP}/mipsel_$MIPS_V.tar.gz


cat > ${P}/CONTROL/control << EOF
Package: enigma2-plugin-extensions-archivczsk
Version: ${PVER}
Architecture: all
Section: extra
Priority: optional
Depends: enigma2-plugin-extensions-subssupport (>=1.5.4)
Recommends: python-html, python-threading, python-json, python-zlib, python-compression, python-codecs, python-email, python-youtube-dl, curl, rtmpdump
Maintainer: mxfitsat@gmail.com
Homepage: https://github.com/mx3L/archivczsk/releases
Description: prehravanie CZ/SK archivov ${VER}
EOF

cat > ${P}/CONTROL/preinst << EOF
#!/bin/sh
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/archivCZSK
exit 0
EOF

cat > ${P}/CONTROL/prerm << EOF
#!/bin/sh
mkdir -p /tmp/archivczsk

if [ -f /usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/categories.xml ];
then
	echo "saving categories.xml to /tmp/archivczsk ..."
	cp /usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/categories.xml /tmp/archivczsk/
fi
if [ -d /usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/resources/data/ ];
then
	echo "saving DATA to /tmp/archivczsk ..."
	cp -R /usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/resources/data/ /tmp/archivczsk/
fi

exit 0
EOF

cat > ${P}/CONTROL/postrm << EOF
#!/bin/sh
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/archivCZSK
exit 0
EOF

cp ${S}/script/postinst ${P}/CONTROL/


chmod 755 ${P}/CONTROL/preinst
chmod 755 ${P}/CONTROL/postinst
chmod 755 ${P}/CONTROL/prerm
chmod 755 ${P}/CONTROL/postrm

mkdir -p ${P}${PLUGINPATH}
mkdir -p ${P}${PLUGINPATH}/locale/cs/LC_MESSAGES/
mkdir -p ${P}${PLUGINPATH}/locale/sk/LC_MESSAGES/
mkdir -p ${P}/usr/lib/enigma2/python/Components/Converter/

cp -rp ${S}/build/plugin/src/* ${P}${PLUGINPATH}
cp -p ${S}/build/plugin/src/converter/* ${P}/usr/lib/enigma2/python/Components/Converter/
touch ${P}${PLUGINPATH}/firsttime

echo "creating locales"
msgfmt ${S}/build/plugin/po/cs.po -o ${P}${PLUGINPATH}/locale/cs/LC_MESSAGES/archivCZSK.mo
msgfmt ${S}/build/plugin/po/sk.po -o ${P}${PLUGINPATH}/locale/sk/LC_MESSAGES/archivCZSK.mo

#echo "compiling to optimized python bytecode"
#python -O -m compileall ${P} 1> /dev/null

echo "cleanup of unnecessary files"
find ${P} -type f -name ".gitignore" -exec rm {} \;
find ${P} -name Makefile.am -exec rm {} \;
rm -rf ${P}${PLUGINPATH}/converter
rm -rf ${P}${PLUGINPATH}/resources/data/*

if ! [ -z "${ADDONS_COMMIT}" ]; then
	${S}/build/plugin/src/script/getaddons.py xbmc_doplnky ${P} $ADDONS_COMMIT
	${S}/build/plugin/src/script/getaddons.py dmd_czech ${P} $ADDONS_COMMIT
	${S}/build/plugin/src/script/getaddons.py custom ${P} $ADDONS_COMMIT
fi


mkdir -p ${P}/tmp/archivczsk
mkdir -p ${P}/tmp/archivczsk/python2.7
mkdir -p ${P}/tmp/archivczsk/python2.6

cp -rp ${DP}/sh4 ${P}/tmp/archivczsk
cp -rp ${DP}/mipsel ${P}/tmp/archivczsk

cp -p ${DP}/Python-2.6/Lib/encodings/utf_8.py ${P}/tmp/archivczsk/python2.6/utf_8.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1251.py ${P}/tmp/archivczsk/python2.6/cp1251.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1252.py ${P}/tmp/archivczsk/python2.6/cp1252.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1253.py ${P}/tmp/archivczsk/python2.6/cp1253.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1254.py ${P}/tmp/archivczsk/python2.6/cp1254.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1256.py ${P}/tmp/archivczsk/python2.6/cp1256.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_6.py ${P}/tmp/archivczsk/python2.6/iso8859_6.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_7.py ${P}/tmp/archivczsk/python2.6/iso8859_7.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_9.py ${P}/tmp/archivczsk/python2.6/iso8859_9.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_15.py ${P}/tmp/archivczsk/python2.6/iso8859_15.py

cp -p ${DP}/Python-2.6/Lib/encodings/hex_codec.py ${P}/tmp/archivczsk/python2.6/hex_codec.py
cp -p ${DP}/Python-2.6/Lib/encodings/string_escape.py ${P}/tmp/archivczsk/python2.7/string_escape.py
cp -p ${DP}/Python-2.6/Lib/encodings/latin_1.py ${P}/tmp/archivczsk/python2.6/latin_1.py
cp -p ${DP}/Python-2.6/Lib/encodings/utf_16.py ${P}/tmp/archivczsk/python2.6/utf_16.py
cp -p ${DP}/Python-2.6/Lib/encodings/idna.py ${P}/tmp/archivczsk/python2.6/idna.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_2.py ${P}/tmp/archivczsk/python2.6/iso8859_2.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1250.py ${P}/tmp/archivczsk/python2.6/cp1250.py
cp -p ${DP}/Python-2.6/Lib/decimal.py ${P}/tmp/archivczsk/python2.6/decimal.py
cp -p ${DP}/Python-2.6/Lib/formatter.py ${P}/tmp/archivczsk/python2.6/formatter.py
cp -p ${DP}/Python-2.6/Lib/markupbase.py ${P}/tmp/archivczsk/python2.6/markupbase.py
cp -p ${DP}/Python-2.6/Lib/HTMLParser.py ${P}/tmp/archivczsk/python2.6/HTMLParser.py
cp -p ${DP}/Python-2.6/Lib/htmlentitydefs.py ${P}/tmp/archivczsk/python2.6/htmlentitydefs.py
cp -p ${DP}/Python-2.6/Lib/htmllib.py ${P}/tmp/archivczsk/python2.6/htmllib.py
cp -p ${DP}/Python-2.6/Lib/sgmllib.py ${P}/tmp/archivczsk/python2.6/sgmllib.py
cp -p ${DP}/Python-2.6/Lib/stringprep.py ${P}/tmp/archivczsk/python2.6/stringprep.py
cp -p ${DP}/Python-2.6/Lib/numbers.py ${P}/tmp/archivczsk/python2.6/numbers.py
cp -p ${DP}/Python-2.6/Lib/subprocess.py ${P}/tmp/archivczsk/python2.6/subprocess.py
cp -p ${DP}/Python-2.6/Lib/_LWPCookieJar.py ${P}/tmp/archivczsk/python2.6/_LWPCookieJar.py
cp -p ${DP}/Python-2.6/Lib/_MozillaCookieJar.py ${P}/tmp/archivczsk/python2.6/_MozillaCookieJar.py
cp -p ${DP}/Python-2.6/Lib/cookielib.py ${P}/tmp/archivczsk/python2.6/cookielib.py
cp -p ${DP}/Python-2.6/Lib/shutil.py ${P}/tmp/archivczsk/python2.6/shutil.py
cp -p ${DP}/Python-2.6/Lib/fnmatch.py ${P}/tmp/archivczsk/python2.6/fnmatch.py
cp -p ${DP}/Python-2.6/Lib/threading.py ${P}/tmp/archivczsk/python2.6/threading.py
cp -p ${DP}/Python-2.6/Lib/zipfile.py ${P}/tmp/archivczsk/python2.6/zipfile.py
cp -p ${DP}/Python-2.6/Lib/httplib.py ${P}/tmp/archivczsk/python2.6/httplib.py
cp -p ${DP}/Python-2.6/Lib/stat.py ${P}/tmp/archivczsk/python2.6/stat.py


cp -p ${DP}/Python-2.7/Lib/encodings/utf_8.py ${P}/tmp/archivczsk/python2.7/utf_8.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1251.py ${P}/tmp/archivczsk/python2.7/cp1251.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1252.py ${P}/tmp/archivczsk/python2.7/cp1252.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1253.py ${P}/tmp/archivczsk/python2.7/cp1253.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1254.py ${P}/tmp/archivczsk/python2.7/cp1254.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1256.py ${P}/tmp/archivczsk/python2.7/cp1256.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_6.py ${P}/tmp/archivczsk/python2.7/iso8859_6.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_7.py ${P}/tmp/archivczsk/python2.7/iso8859_7.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_9.py ${P}/tmp/archivczsk/python2.7/iso8859_9.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_15.py ${P}/tmp/archivczsk/python2.7/iso8859_15.py

cp -p ${DP}/Python-2.7/Lib/encodings/hex_codec.py ${P}/tmp/archivczsk/python2.7/hex_codec.py
cp -p ${DP}/Python-2.7/Lib/encodings/string_escape.py ${P}/tmp/archivczsk/python2.7/string_escape.py
cp -p ${DP}/Python-2.7/Lib/encodings/latin_1.py ${P}/tmp/archivczsk/python2.7/latin_1.py
cp -p ${DP}/Python-2.7/Lib/encodings/utf_16.py ${P}/tmp/archivczsk/python2.7/utf_16.py
cp -p ${DP}/Python-2.7/Lib/encodings/idna.py ${P}/tmp/archivczsk/python2.7/idna.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_2.py ${P}/tmp/archivczsk/python2.7/iso8859_2.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1250.py ${P}/tmp/archivczsk/python2.7/cp1250.py
cp -p ${DP}/Python-2.7/Lib/decimal.py ${P}/tmp/archivczsk/python2.7/decimal.py
cp -p ${DP}/Python-2.7/Lib/formatter.py ${P}/tmp/archivczsk/python2.7/formatter.py
cp -p ${DP}/Python-2.7/Lib/markupbase.py ${P}/tmp/archivczsk/python2.7/markupbase.py
cp -p ${DP}/Python-2.7/Lib/HTMLParser.py ${P}/tmp/archivczsk/python2.7/HTMLParser.py
cp -p ${DP}/Python-2.7/Lib/htmlentitydefs.py ${P}/tmp/archivczsk/python2.7/htmlentitydefs.py
cp -p ${DP}/Python-2.7/Lib/htmllib.py ${P}/tmp/archivczsk/python2.7/htmllib.py
cp -p ${DP}/Python-2.7/Lib/sgmllib.py ${P}/tmp/archivczsk/python2.7/sgmllib.py
cp -p ${DP}/Python-2.7/Lib/stringprep.py ${P}/tmp/archivczsk/python2.7/stringprep.py
cp -p ${DP}/Python-2.7/Lib/numbers.py ${P}/tmp/archivczsk/python2.7/numbers.py
cp -p ${DP}/Python-2.7/Lib/subprocess.py ${P}/tmp/archivczsk/python2.7/subprocess.py
cp -p ${DP}/Python-2.7/Lib/_LWPCookieJar.py ${P}/tmp/archivczsk/python2.7/_LWPCookieJar.py
cp -p ${DP}/Python-2.7/Lib/_MozillaCookieJar.py ${P}/tmp/archivczsk/python2.7/_MozillaCookieJar.py
cp -p ${DP}/Python-2.7/Lib/cookielib.py ${P}/tmp/archivczsk/python2.7/cookielib.py
cp -p ${DP}/Python-2.7/Lib/shutil.py ${P}/tmp/archivczsk/python2.7/shutil.py
cp -p ${DP}/Python-2.7/Lib/fnmatch.py ${P}/tmp/archivczsk/python2.7/fnmatch.py
cp -p ${DP}/Python-2.7/Lib/threading.py ${P}/tmp/archivczsk/python2.7/threading.py
cp -p ${DP}/Python-2.7/Lib/zipfile.py ${P}/tmp/archivczsk/python2.7/zipfile.py
cp -p ${DP}/Python-2.7/Lib/httplib.py ${P}/tmp/archivczsk/python2.7/httplib.py
cp -p ${DP}/Python-2.7/Lib/stat.py ${P}/tmp/archivczsk/python2.7/stat.py


tar -C ${P} -czf ${B}/data.tar.gz . --exclude=CONTROL
tar -C ${P}/CONTROL -czf ${B}/control.tar.gz .

echo "2.0" > ${B}/debian-binary

cd ${B}
ls -la
ar -r ${PKG}.ipk ./debian-binary ./control.tar.gz ./data.tar.gz
ar -r ${PKG}.deb ./debian-binary ./control.tar.gz ./data.tar.gz
cd ${D}

rm -rf ${P}
rm -rf ${B}
rm -rf ${S}

#rm -rf ${DP}