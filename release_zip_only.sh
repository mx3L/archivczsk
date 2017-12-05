# a='hello'
# b='world'
# c=$a$b
# echo $c

# cez args spravit

if [ -z $1 ];
then
	echo " "
	echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	echo "!!!! first args must be a version number etc 0.75 !!!!"
	echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	echo " "
else
	version=$1
	D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
	cd $D
	rm -rf archivCZSK/
	sed -i "s/version = \".*\"/version = \"$version\"/g" build/plugin/src/version.py
	cp -a build/plugin/src/. archivCZSK/
	mkdir archivCZSK/locale
	mkdir archivCZSK/locale/sk
	mkdir archivCZSK/locale/cs
	mkdir archivCZSK/locale/cs/LC_MESSAGES
	mkdir archivCZSK/locale/sk/LC_MESSAGES
	msgfmt build/plugin/po/sk.po -o archivCZSK/locale/sk/LC_MESSAGES/archivCZSK.mo
	msgfmt build/plugin/po/cs.po -o archivCZSK/locale/cs/LC_MESSAGES/archivCZSK.mo
	
	zip -FS -q -r build/plugin/update/version/archivczsk-$version.zip archivCZSK -x "*.py[oc] *.sw[onp]" -x "*converter/*" -x "*Makefile.am" -x "*categories.xml" -x "*.gitignore"
	rm -rf archivCZSK/
	cp build/plugin/src/changelog.txt build/plugin/update/version/changelog-$version.txt
	sed -i "s/version=\".*\">/version=\"$version\">/g" build/plugin/update/app.xml
	echo " "
	echo "****************************************************************"
	echo "**** ZIP & changelog create to build/plugin/update/version/ ****"
	echo "**** Please check this file: build/plugin/update/app.xml    ****"
	echo "****                         build/plugin/src/version.py    ****"
	echo "****************************************************************"
	echo " "
fi
