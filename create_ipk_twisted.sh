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


############ SCRIPT ############
D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
P=${D}/ipkgtwisted.tmp.$$
B=${D}/ipkgtwisted.build.$$
Tw=${D}/build/twisted
PKG=${D}/twisted-16-2-0-fix

pushd ${D} &> /dev/null

popd &> /dev/null

rm -rf ${D}/ipkgtwisted.tmp*
rm -rf ${D}/ipkgtwisted.build*

mkdir -p ${P}
mkdir -p ${P}/CONTROL
mkdir -p ${B}

cat > ${P}/CONTROL/control << EOF
Package: python-twisted
Version: 16.2.0
Architecture: all
Section: extra
Priority: optional
Depends: enigma2-plugin-extensions-archivczsk (>=0.74)
Recommends: python-html, python-threading
Maintainer: ferko
Homepage: https://github.com/mx3L/archivczsk/releases
Description: archivCZSK fix BlackHole image
EOF

cat > ${P}/CONTROL/preinst << EOF
#!/bin/sh
echo "preinst"
exit 0
EOF

cat > ${P}/CONTROL/prerm << EOF
#!/bin/sh
echo "prerm"
exit 0
EOF

cat > ${P}/CONTROL/postinst << EOF
#!/bin/sh
echo "installing twisted"
if [ -d $PSitePackages];
then
	if [ -d /usr/lib/python2.7/site-packages/twisted ];
	then
		echo "twisted found... REINSTALL"
		cp -R /usr/lib/python2.7/site-packages/twisted /usr/lib/python2.7/site-packages/twisted_origin_backup
		echo "create backup to twisted_origin_backup"
		rm -rf /usr/lib/python2.7/site-packages/twisted
		cp -R /tmp/twisted /usr/lib/python2.7/site-packages/twisted
	else
		echo "twisted not found... INSTALL"
		cp -R /tmp/twisted /usr/lib/python2.7/site-packages/twisted
	fi
else
	echo "python 2.7 site-packages dir not found!!!"
fi
echo "Install twisted successfully, please reboot device."
exit 0
EOF

cat > ${P}/CONTROL/postrm << EOF
#!/bin/sh
echo "postrm"
exit 0
EOF

chmod 755 ${P}/CONTROL/preinst
chmod 755 ${P}/CONTROL/postinst
chmod 755 ${P}/CONTROL/prerm
chmod 755 ${P}/CONTROL/postrm

mkdir -p ${P}/tmp

cp -R ${Tw} ${P}/tmp

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