#!/bin/sh
D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
P=${D}/tmp/
PLUGINPATH="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK"

HOST="192.168.7.105"
USERNAME="root"
PASSWORD="openpli3"

if [ ! -z $1 ];
then
	HOST=$1
fi

if [ ! -z $2 ];
then
	USERNAME=$2
fi
if [ ! -z $3 ];
then
	PASSWORD=$3
fi

echo "connection parameters: $HOST $USERNAME $PASSWORD"

echo "creating archivczsk.tar.gz"
rm ${D}/archivyczsk.tar.gz 2> /dev/null

mkdir -p ${P}${PLUGINPATH}
mkdir -p ${P}${PLUGINPATH}/locale/cs/LC_MESSAGES/
mkdir -p ${P}${PLUGINPATH}/locale/sk/LC_MESSAGES/
mkdir -p ${P}/usr/lib/enigma2/python/Components/Converter/

cp -rp ${D}/build/plugin/src/* ${P}${PLUGINPATH}
cp -p ${D}/build/plugin/src/converter/* ${P}/usr/lib/enigma2/python/Components/Converter/

msgfmt ${D}/build/plugin/po/cs.po -o ${P}${PLUGINPATH}/locale/cs/LC_MESSAGES/archivCZSK.mo
msgfmt ${D}/build/plugin/po/sk.po -o ${P}${PLUGINPATH}/locale/sk/LC_MESSAGES/archivCZSK.mo

#echo "compiling to optimized python bytecode"
#python -O -m compileall ${P} 1> /dev/null


echo "cleanup of unnecessary files"
find ${P} -name "*.po" -exec rm {} \;
find ${P} -name "*.pyo" -exec rm {} \;
find ${P} -name "*.pyc" -exec rm {} \;
find ${P} -name Makefile.am -exec rm {} \;

rm -rf ${P}${PLUGINPATH}/converter
rm -rf ${P}${PLUGINPATH}/engine/player/servicemp4

${D}/build/plugin/src/script/getaddons.py xbmc_doplnky ${P}
${D}/build/plugin/src/script/getaddons.py dmd_czech ${P}
${D}/build/plugin/src/script/getaddons.py custom ${P}

tar -C ${P} -czf archivyczsk.tar.gz .

echo "uploading archivczsk.tar.gz to $HOST"
ftp -n $HOST <<EOFFTP
user $USERNAME $PASSWORD
binary
cd /tmp
put archivyczsk.tar.gz
bye
EOFFTP

rm archivyczsk.tar.gz 2> /dev/null
rm -rf ${P}

echo "installing archivCZSK on $HOST"
sshpass -p $PASSWORD ssh $USERNAME@$HOST << EOFSSH
rm -rf $PLUGINPATH
tar -C / -xzf /tmp/archivyczsk.tar.gz
rm /tmp/archivyczsk.tar.gz
killall enigma2
EOFSSH


echo "archivCZSK was succesfully installed on $HOST"
echo "restarting enigma2"
