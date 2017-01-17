AC_INIT([enigma2-plugin-extensions-archivczsk],[0.74])
AM_INIT_AUTOMAKE([dist-bzip2 foreign no-define tar-pax])

# Silent rules are available since 1.11, but older versions
# are still in use. So don't use them unconditionally.
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])

AC_CONFIG_MACRO_DIR([m4])

AC_PATH_PROG(MSGFMT, msgfmt, AC_MSG_ERROR(Could not find msgfmt))
AM_PATH_PYTHON

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

AC_CONFIG_FILES([
Makefile

plugin/Makefile
plugin/po/Makefile
plugin/src/Makefile
plugin/src/converter/Makefile
plugin/src/client/Makefile
plugin/src/gui/Makefile
plugin/src/gui/icon/Makefile
plugin/src/gui/icon/spinner/Makefile
plugin/src/gui/icon/buttons/Makefile
plugin/src/gui/skins/Makefile
plugin/src/engine/Makefile
plugin/src/engine/tools/Makefile
plugin/src/engine/exceptions/Makefile
plugin/src/engine/handlers/Makefile
plugin/src/engine/player/Makefile
plugin/src/resources/Makefile
plugin/src/resources/repositories/Makefile
plugin/src/resources/repositories/custom/Makefile
plugin/src/resources/repositories/dmd_czech/Makefile
plugin/src/resources/repositories/xbmc_doplnky/Makefile
plugin/src/resources/libraries/Makefile
plugin/src/resources/libraries/iso8601/Makefile
plugin/src/resources/libraries/m3u8/Makefile
plugin/src/resources/libraries/simplejson/Makefile
plugin/src/script/Makefile
])
AC_OUTPUT

