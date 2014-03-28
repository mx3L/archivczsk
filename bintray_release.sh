#!/bin/sh

REPO_NAME=generic
PACKAGE_NAME=enigma2-plugin-extensions-archivczsk
VERSION_NAME=$1

curl --data "\"name\": version, \"desc\": $VERSION_NAME" \
	-umx3l:$bintray_api_key \
	https://api.bintray.com/packages/mx3l/$REPO_NAME/$PACKAGE_NAME/versions

curl -vT $2 \
    -umx3l:$bintray_api_key \
    https://api.bintray.com/content/mx3l/$REPO_NAME/$PACKAGE_NAME/$VERSION_NAME/