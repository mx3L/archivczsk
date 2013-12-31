AC_INIT([enigma2-plugin-extensions-archivczsk],[0.70])
AM_INIT_AUTOMAKE([dist-bzip2 foreign no-define tar-pax])
AC_CONFIG_HEADERS([enigma2-plugins-config.h])

# Silent rules are available since 1.11, but older versions
# are still in use. So don't use them unconditionally.
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])

AC_USE_SYSTEM_EXTENSIONS
AC_SYS_LARGEFILE

AC_PROG_CC
AC_PROG_CXX
m4_ifdef([LT_INIT], [LT_INIT], [AC_PROG_LIBTOOL])
AC_CONFIG_MACRO_DIR([m4])

AC_PATH_PROG(MSGFMT, msgfmt, AC_MSG_ERROR(Could not find msgfmt))

AM_PATH_PYTHON
AX_PYTHON_DEVEL
AX_PKG_SWIG
AX_SWIG_ENABLE_CXX
AX_SWIG_PYTHON
AX_PTHREAD

TUXBOX_APPS_DVB

PKG_CHECK_MODULES(ENIGMA2, enigma2)
PKG_CHECK_MODULES(GSTREAMER, gstreamer-0.10 gstreamer-pbutils-0.10)
PKG_CHECK_MODULES(LIBCRYPTO, libcrypto)

AC_ARG_WITH(debug,
	AS_HELP_STRING([--without-debug],[disable debugging code]),
	[with_debug="$withval"],[with_debug="yes"])
if test "$with_debug" = "yes"; then
	DEBUG_CFLAGS="-ggdb3"
	AC_DEFINE([DEBUG],[1],[Define to 1 to enable debugging code])
fi

AC_ARG_WITH(po,
	AS_HELP_STRING([--with-po],[enable updating of po files]),
	[with_po="$withval"],[with_po="no"])
if test "$with_po" = "yes"; then
	AC_PATH_PROG(MSGINIT, msginit)
	AC_PATH_PROG(MSGMERGE, msgmerge)
	AC_PATH_PROG(MSGUNIQ, msguniq)
	AC_PATH_PROG(XGETTEXT, xgettext)
	if test -z "$MSGINIT" -o -z "$MSGMERGE" -o -z "$MSGUNIQ" -o -z "$XGETTEXT"; then
		AC_MSG_ERROR([Could not find required gettext tools])
	fi
fi
AM_CONDITIONAL(UPDATE_PO, test "$with_po" = "yes")

CPPFLAGS="$CPPFLAGS $PYTHON_CPPFLAGS -include Python.h -include enigma2-plugins-config.h"
CFLAGS="$CFLAGS $DEBUG_CFLAGS -Wall"
CXXFLAGS="$CXXFLAGS $DEBUG_CFLAGS -Wall $GSTREAMER_CFLAGS $ENIGMA2_CFLAGS $PTHREAD_CFLAGS"

AC_CONFIG_FILES([
Makefile

plugin/Makefile
plugin/po/Makefile
plugin/meta/Makefile
plugin/src/Makefile
plugin/src/converter/Makefile
plugin/src/client/Makefile
plugin/src/gui/Makefile
plugin/src/gui/icon/Makefile
plugin/src/gui/skins/Makefile
plugin/src/gui/icon/mplayer/Makefile
plugin/src/gui/icon/spinner/Makefile
plugin/src/gui/icon/buttons/Makefile
plugin/src/engine/Makefile
plugin/src/engine/tools/Makefile
plugin/src/engine/exceptions/Makefile
plugin/src/engine/handlers/Makefile
plugin/src/engine/player/Makefile
plugin/src/engine/player/subtitles/Makefile
plugin/src/engine/player/subtitles/fonts/Makefile
plugin/src/engine/player/subtitles/parsers/Makefile
plugin/src/engine/player/servicemp4/Makefile
plugin/src/resources/Makefile
plugin/src/resources/repositories/Makefile
plugin/src/resources/repositories/custom/Makefile
plugin/src/resources/repositories/dmd_czech/Makefile
plugin/src/resources/repositories/xbmc_doplnky/Makefile
plugin/src/resources/libraries/Makefile
plugin/src/resources/libraries/simplejson/Makefile
plugin/src/streams/Makefile
plugin/src/script/Makefile
])
AC_OUTPUT
