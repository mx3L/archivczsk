SUMMARY = "Plugin for watching sk/cs archives of tv stations"
HOMEPAGE = "https://github.com/mx3L/archivczsk"
LICENSE = "GPLv2"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/GPL-2.0;md5=801f80980d171dd6425610833a22dbe6"
PR = "r0"

ADDONS_COMMIT = "528cad1a88f6b8eab26d42ac8997d3ca4d8c7da4"

RDEPENDS_${PN} = "enigma2-plugin-extensions-subssupport (>= 1.5.4) \
    curl \
    python-codecs \
    python-compression \
    python-email \
    python-html \
    python-json \
    python-threading \
    python-zlib \
    rtmpdump"

SRCREV = "3c1af45c32959e43fad58d57f4119aeb4c11fd64"
SRC_URI = "git://github.com/mx3L/archivczsk.git;branch=test"

S = "${WORKDIR}/git/build"

FILES_${PN} = "${libdir}/enigma2/python/Plugins/Extensions/archivCZSK \
    ${libdir}/enigma2/python/Components/Converter"

inherit autotools-brokensep

pkg_postinst_${PN} () {
    cd ${libdir}/enigma2/python/Plugins/Extensions/archivCZSK/script
    python getaddons.py xbmc_doplnky / ${ADDONS_COMMIT}
    python getaddons.py dmd_czech / ${ADDONS_COMMIT}
    python getaddons.py custom / ${ADDONS_COMMIT}
}

pkg_postrm_${PN} () {
    rm -rf ${libdir}/enigma2/python/Plugins/Extensions/archivCZSK/resources/repositories
}

