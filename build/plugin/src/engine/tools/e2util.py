from enigma import getDesktop

def get_desktop_width_and_height():
    desktop_size = getDesktop(0).size()
    return (desktop_size.width(), desktop_size.height())

