#!/bin/sh

platform="mipsel"
force=$1
openpli=$2
BASEDIR=$(dirname $0)

echo "GStreamer pluginy pre archivCZSK"
if [ `ls -al /usr/lib/python2.7 | grep urllib.pyo | wc -l` -gt 0 ]; then
	platform="mips32el"
fi


if [ "$platform" != "mipsel" -a "$platform" != "mips32el" ]
then
	echo "Zadali ste nespravnu platformu $platform !!, spuste instalacny skript znova"
	exit 1
else 
	echo "Zvolena platforma: $platform"
fi

if [ "$force" != "N" ]
then
	echo "Balicky budu preinstalovane"
	force="A"
fi


check_pkg ()
{
	echo $(opkg list_installed|grep $1|wc -l)
}

reinstall_pkg ()
{
	local package=$1
	echo "Pokusam sa instalovat $package z feedu"
	opkg --force-reinstall install $package > /dev/null
	if [ "$(check_pkg $package)" != "0" ]
	then 
		echo "Instalacia $package bola uspesna"
	else
		echo "$package sa nenachadza vo feede"
		echo "Instalacia $package nebola uspesna,,"
	fi	
}
install_pkg ()
{
	local package=$1
	echo "Hladam $package balicek"
	if [ "$(check_pkg $package)" != "0" ]
	then
		echo "Balicek $package je uz nainstalovany"
	else
		echo "Balicek $package nie je nainstalovany"
		echo "Pokusim sa instalovat $package z feedu"
		opkg --force-reinstall install $package > /dev/null
		if [ "$(check_pkg $package)" != "0" ]
		then 
			echo "Instalacia $package bola uspesna"
		else
			echo "$package sa nenachadza vo feede"
			echo "Instalacia $package bola neuspesna..."
		fi
	fi	
}
echo $BASEDIR

echo "Aktualizujem feedy..."
opkg update > /dev/null

echo "Prebieha instalacia..."
if [ "$platform" == "mipsel" ]
then
	if [ "$force" == "N" ]
	then
		install_pkg gst-plugin-fragmented
		install_pkg gst-plugin-matroska
		install_pkg gst-plugin-avi
		install_pkg gst-plugin-asf
		install_pkg gst-plugin-rtsp
		install_pkg gst-plugin-mms
		install_pkg gst-plugin-flv 
		install_pkg gst-plugin-rtmp 
		install_pkg gst-plugin-isomp4
		install_pkg librtmp0
	else
		reinstall_pkg gst-plugin-flv 
		reinstall_pkg gst-plugin-rtmp
		reinstall_pkg librtmp0
	fi

elif [ "$platform" == "mips32el" ]
then
	if [ "$force" == "N" ]
	then
		install_pkg gst-plugins-bad-fragmented
		install_pkg gst-plugins-good-matroska
		install_pkg gst-plugins-good-avi
		install_pkg gst-plugins-ugly-asf
		install_pkg gst-plugins-good-rtsp
		install_pkg gst-plugins-bad-mms
		install_pkg gst-plugins-good-flv 
		install_pkg gst-plugins-bad-rtmp 
		install_pkg gst-plugins-good-isomp4
		install_pkg librtmp0
		install_pkg librtmp1
	else
		reinstall_pkg gst-plugins-good-flv 
		reinstall_pkg gst-plugins-bad-rtmp 
		reinstall_pkg librtmp0
		reinstall_pkg librtmp1
	fi
else
	echo "Zvolili ste nespravnu platformu $platform, zvolte bud mipsel alebo mips32el platformu"
	exit 1
fi

exit 0
