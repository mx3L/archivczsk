#!/bin/bash

D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
PLUGINPATH="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK"

if [ ! -z $1 ];
then
	E2_HOST=$1
fi

if [ ! -z $2 ];
then
	E2_USERNAME=$2
fi
if [ ! -z $3 ];
then
	E2_PASSWORD=$3
fi

echo "connection parameters: $E2_HOST $E2_USERNAME $E2_PASSWORD"
echo "creating ipk..."
${D}/create_ipk_all.sh > /dev/null
IPK_PATH=$(find ${D} -maxdepth 1 -mmin 1 -name "*.ipk")
IPK_NAME=$(basename $IPK_PATH)

echo "uploading ipk to $E2_HOST..."
ftp -n $E2_HOST <<EOFFTP
user $E2_USERNAME $E2_PASSWORD
binary
cd /tmp
lcd ${D}
put $IPK_NAME
bye
EOFFTP

echo "installing archivCZSK on $E2_HOST"
sshpass -p $E2_PASSWORD ssh -t $E2_USERNAME@$E2_HOST << EOFSSH
opkg remove enigma2-plugin-extensions-archivczsk
opkg install /tmp/$IPK_NAME
rm /tmp/$IPK_NAME
killall enigma2
EOFSSH

echo "restarting enigma2"
