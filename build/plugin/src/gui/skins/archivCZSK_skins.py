VideoAddonsContentScreen_HD = """
        <screen position="center,center" size="900,576" title="ArchivyCZSK" flags="wfBorder" transparent="0">
            <widget backgroundColor="#9f1313" font="Regular;20" halign="center" name="key_red" position="8,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#1f771f" font="Regular;20" halign="center" name="key_green" position="231,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#a08500" font="Regular;20" halign="center" name="key_yellow" position="454,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#18188b" font="Regular;20" halign="center" name="key_blue" position="677,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget name="menu" position="12,62" scrollbarMode="showNever" size="435,427" transparent="1" />
            <widget alphatest="on" name="image" position="543,124" size="256,256" zPosition="2" />
            <widget font="Regular; 25" foregroundColor="yellow" halign="center" name="title" position="472,64" size="379,40" transparent="1" />
            <widget font="Regular;20" foregroundColor="yellow" halign="left" name="author" position="487,402" size="379,25" transparent="1" />
            <widget font="Regular;20" foregroundColor="yellow" halign="left" name="version" position="487,439" size="379,25" transparent="1" />
            <widget font="Regular;20" foregroundColor="white" halign="left" name="about" position="487,475" size="379,100" transparent="1" />
            <widget font="Regular;20" foregroundColor="white" halign="left" name="tip_label" position="60,540" size="397,25" transparent="1" />
            <widget name="tip_pixmap" alphatest="on" zPosition="2" position="14,539" size="35,25" />
            <widget name="status_label" position="11,497" size="300,25" font="Regular; 16"  transparent="1" halign="left" valign="center" zPosition="2" foregroundColor="white" />
        </screen>
        """


VideoAddonsContentScreen_SD = """
        <screen position="center,center" size="720,576" title="ArchivCZSK" >
            <widget name="key_red" position="8,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="186,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="364,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="542,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="menu" position="0,55" size="330,485" transparent="1" scrollbarMode="showOnDemand" />
            <widget name="image" position="407,90" zPosition="2" size="256,256" alphatest="on" />
            <widget name="title" position="350,55" size="370,25" halign="center" font="Regular;22" transparent="1" foregroundColor="yellow" />
            <widget name="author" position="350,355" size="370,25" halign="left" font="Regular;20" transparent="1" foregroundColor="yellow" />
            <widget name="version" position="350,390" size="370,25" halign="left" font="Regular;20" transparent="1" foregroundColor="yellow" />
            <widget name="about" position="350,425" size="370,100" halign="left" font="Regular;20" transparent="1" foregroundColor="white" />
            <ePixmap position="0,545" size="35,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/key_info.png"  zPosition="3" transparent="1" alphatest="on" />
        </screen>"""
            
VideoAddonsContentScreen = """
        <screen position="center,center" size="720,576" flags="wfNoBorder" title="ArchivCZSK" >
            <widget name="key_red" position="8,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="186,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="364,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="542,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="path_label" position="5,55" size="600,25" halign="left" font="Regular;22" transparent="1" foregroundColor="yellow" />
	    <widget name="menu" position="0,55" size="330,485" transparent="1" scrollbarMode="showOnDemand" />
            <widget name="image" position="407,90" zPosition="2" size="256,256" alphatest="on" />
            <widget name="title" position="350,55" size="370,25" halign="left" font="Regular;22" transparent="1" foregroundColor="yellow" />
            <widget name="author" position="350,355" size="370,25" halign="left" font="Regular;20" transparent="1" foregroundColor="yellow" />
            <widget name="version" position="350,390" size="370,25" halign="left" font="Regular;20" transparent="1" foregroundColor="yellow" />
            <widget name="about" position="350,425" size="370,100" halign="left" font="Regular;20" transparent="1" foregroundColor="white" />
            <ePixmap position="0,545" size="35,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/key_info.png"  zPosition="3" transparent="1" alphatest="on" />
        </screen>"""

        
ContentScreen_SD = """
        <screen position="center,center" size="720,576" flags="wfNoBorder" title="ArchivCZSK" >
            <widget name="key_red" position="8,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="186,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="364,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="542,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            
            <widget name="path_label" position="15,60" size="700,25" halign="left" font="Regular;19" transparent="1" foregroundColor="#C4C4C4" />
            <eLabel position="15,90" size="700,  1" zPosition="1" backgroundColor="#C4C4C4" />
            
            <widget name="menu" position="0,95" size="720,405" transparent="1" scrollbarMode="showOnDemand" />
            <widget name="tip_pixmap" position="5,540" size="35,25" zPosition="2" alphatest="on" />
            <widget name="tip_label" position="45,540" size="535,25" valign="center" halign="left" zPosition="2" font="Regular;18" transparent="1" foregroundColor="white" />
        </screen>
        """
  #<widget alphatest="on" name="path_pixmap" position="10,62" size="32,32" zPosition="2" />

ContentScreen_HD_IMG = """
        <screen position="center,center" size="1100,575" title="ContentScreen" backgroundColor="#28080808">
            <widget backgroundColor="#9f1313" font="Regular;20" halign="center" name="key_red" position="8,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#1f771f" font="Regular;20" halign="center" name="key_green" position="231,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#a08500" font="Regular;20" halign="center" name="key_yellow" position="454,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#18188b" font="Regular;20" halign="center" name="key_blue" position="677,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget name="path_label" position="20,65" size="1060,25" halign="left" font="Regular;19" transparent="1" foregroundColor="#C4C4C4" />
            <eLabel position="20,95" size="1060,1" zPosition="1" backgroundColor="#C4C4C4" />
            <widget name="menu" position="12,110" scrollbarMode="showOnDemand" size="680,419" transparent="1" />
            <widget alphatest="on" name="image" position="715,110" size="370,300" zPosition="2" />
            <widget font = "Regular; 16" foregroundColor = "white" halign = "left" name = "status_label" position = "12,508" size = "535,25" transparent = "1" valign = "center" zPosition = "2" /> 
            <widget alphatest="on" name="tip_pixmap" position="9,544" size="35,25" zPosition="2" />
            <widget font="Regular;18" foregroundColor="white" halign="left" name="tip_label" position="55,548" size="493,25" transparent="1" valign="center" zPosition="2" />
        </screen>
             """
  
  
ContentScreen_HD = """
        <screen position="center,center" size="900,575" title="ContentScreen">
            <widget backgroundColor="#9f1313" font="Regular;20" halign="center" name="key_red" position="8,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#1f771f" font="Regular;20" halign="center" name="key_green" position="231,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#a08500" font="Regular;20" halign="center" name="key_yellow" position="454,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#18188b" font="Regular;20" halign="center" name="key_blue" position="677,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            
            <widget name="path_label" position="15,65" size="870,25" halign="left" font="Regular;19" transparent="1" foregroundColor="#C4C4C4" />
            <eLabel position="15,95" size="870,1" zPosition="1" backgroundColor="#C4C4C4" />
            <widget name="menu" position="10,110" scrollbarMode="showOnDemand" size="880,420" transparent="1" />
            <widget font = "Regular; 16" foregroundColor = "white" halign = "left" name = "status_label" position = "12,508" size = "535,25" transparent = "1" valign = "center" zPosition = "2" /> 
            <widget alphatest="on" name="tip_pixmap" position="9,544" size="35,25" zPosition="2" />
            <widget font="Regular;18" foregroundColor="white" halign="left" name="tip_label" position="55,548" size="493,25" transparent="1" valign="center" zPosition="2" />
        </screen>
             """

StreamContentScreen_SD = """
        <screen position="center,center" size="720,576" flags="wfNoBorder" title="ArchivCZSK" >
            <widget name="key_red" position="8,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="186,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="364,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="542,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="path_label" position="15,60" size="700,25" halign="left" font="Regular;19" transparent="1" foregroundColor="#C4C4C4" />
            <eLabel position="15,90" size="700,  1" zPosition="1" backgroundColor="#C4C4C4" />
            <widget name="menu" position="0,95" size="720,405" transparent="1" scrollbarMode="showOnDemand" />
            <widget name="tip_pixmap" position="5,540" size="35,25" zPosition="2" alphatest="on" />
            <widget name="tip_label" position="45,540" size="535,25" valign="center" halign="left" zPosition="2" font="Regular;18" transparent="1" foregroundColor="white" />
        </screen>
        """
        
        
StreamContentScreen_HD = """
        <screen backgroundColor="background" name="StreamContentScreen_HD" position="center,90" size="900,575" title="Streams">
            <widget backgroundColor="#9f1313" font="Regular;20" halign="center" name="key_red" position="8,520" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#1f771f" font="Regular;20" halign="center" name="key_green" position="231,520" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#a08500" font="Regular;20" halign="center" name="key_yellow" position="454,520" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#18188b" font="Regular;20" halign="center" name="key_blue" position="677,520" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget name="menu" position="13,102" scrollbarMode="showOnDemand" size="530,330" transparent="1" />
            <widget alphatest="on" name="tip_pixmap" position="8,442" size="35,25" zPosition="2" />
            <widget font="Regular;18" foregroundColor="white" halign="left" name="tip_label" position="55,442" size="535,25" transparent="1" valign="center" zPosition="2" />
            <widget backgroundColor="background" font="Regular; 24" name="streaminfo_label" position="604,120" size="226,34" />
            <widget backgroundColor="background" font="Regular; 20" foregroundColor="#e5b243" name="protocol_label" position="579,170" size="167,25" />
            <widget backgroundColor="background" font="Regular; 20" name="protocol" position="771,169" size="85,25" />
            <widget backgroundColor="background" font="Regular; 20" foregroundColor="#e5b243" name="playdelay_label" position="580,207" size="167,25" />
            <widget backgroundColor="background" font="Regular; 34" foregroundColor="#e5b243" halign="center" name="archive_label" position="32,6" size="835,34" />
            <widget backgroundColor="background" font="Regular; 20" name="playdelay" position="770,207" size="85,25" />
            <widget backgroundColor="background" font="Regular; 20" name="rtmpbuffer" position="769,244" size="85,25" />
            <widget backgroundColor="background" font="Regular; 20" foregroundColor="#e5b243" name="rtmpbuffer_label" position="580,244" size="167,25" />
            <widget backgroundColor="background" font="Regular; 20" foregroundColor="#e5b243" name="playerbuffer_label" position="581,284" size="167,25" />
            <widget backgroundColor="background" font="Regular; 20" name="playerbuffer" position="769,284" size="85,25" />
            <widget alphatest="on" backgroundColor="background" name="livestream_pixmap" position="8,442" size="35,25" zPosition="2" />
        </screen>"""

        
ContentMenuScreen_HD = """
        <screen name="CtxMenu" position="center,center" size="500,300">
            <widget name="menu" position="0,0" size="500,290" scrollbarMode="showOnDemand" />
        </screen>"""
        
ItemInfoScreen_HD = """
        <screen name="InfoScreen" position="center,center" size="1100,600" title="Info">
            <widget font="Regular;22" foregroundColor="yellow" name="genre" position="435,52" size="613,30" transparent="1" />
            <widget font="Regular;22" foregroundColor="yellow" name="year" position="435,106" size="613,30" transparent="1" />
            <widget font="Regular;22" foregroundColor="yellow" name="rating" position="435,158" size="613,30" transparent="1" />
            <widget font="Regular;23" foregroundColor="white" name="plot" position="433,266" size="645,310" transparent="1" />
            <widget alphatest="on" name="img" position="8,7" size="402,570" zPosition="2" />
        </screen>
        """

ItemInfoScreen_SD = """
        <screen position="center,center" size="720,576" title="Info" >
            <widget name="genre" position="320,50" size="400,30" font="Regular;22" transparent="1" foregroundColor="yellow" />
            <widget name="year" position="320,90" size="400,30" font="Regular;22" transparent="1" foregroundColor="yellow" />
            <widget name="rating" position="320,130" size="400,30" font="Regular;22" transparent="1" foregroundColor="yellow" />
            <widget name="plot" position="0,310" size="720,306" font="Regular;23" transparent="1" foregroundColor="white" />
            <widget name="img" position="10,0" zPosition="2" size="300,300"  alphatest="on"/>
        </screen>"""
        
VideoPlayerInfoScreen_HD = """
        <screen position="center,center" size="900,575" title="ContentScreen">
            <widget backgroundColor="#9f1313" font="Regular;20" halign="center" name="key_red" position="8,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#1f771f" font="Regular;20" halign="center" name="key_green" position="231,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#a08500" font="Regular;20" halign="center" name="key_yellow" position="454,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#18188b" font="Regular;20" halign="center" name="key_blue" position="677,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget name="detected player" position="24,81" size="222,31" font="Regular; 26" />
            <widget name="detected player_val" position="264,81" size="222,31" font="Regular; 26" />
            <widget name="protocol" position="33,135" size="340,30"  foregroundColor="#e5b243" font="Regular; 24" />
            <widget name="container" position="33,317" size="340,30"  font="Regular; 24" foregroundColor="#e5b243" />
            <widget name="protocol_list" position="46,174" size="355,129" />
            <widget name="container_list" position="46,357" size="355,206" />
            <widget name="info_scrolllabel" position="443,135" size="434,428" valign="top" font="Regular; 19"/>
        </screen>
             """

VideoPlayerInfoScreen_SD = """
        <screen position="center,center" size="720,576" flags="wfNoBorder" title="ArchivCZSK" >
            <widget name="key_red" position="8,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="186,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="364,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="542,5" zPosition="1" size="170,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            
            <widget name="detected player" position="24,81" size="222,31" font="Regular; 26" />
            <widget name="detected player_val" position="264,81" size="222,31" font="Regular; 26" />
            <widget name="protocol" position="33,135" size="340,30"  foregroundColor="#e5b243" font="Regular; 24" />
            <widget name="container" position="33,317" size="340,30"  font="Regular; 24" foregroundColor="#e5b243" />
            <widget name="protocol_list" position="46,174" size="355,129" />
            <widget name="container_list" position="46,357" size="355,206" />
            <widget name="info_scrolllabel" position="443,135" size="250,400" valign="top" font="Regular; 19"/>
        </screen>
             """


ContextMenuScreen = """
        <screen name="ContextMenuScreen" position="center,center" size="500,300">
            <widget name="img" position="10,13" size="35,25" alphatest="on" />
            <widget name="name" position="61,10" size="424,60" halign="center" foregroundColor="#e5b243" font="Regular; 23" />
            <widget name="menu" position="1,81" scrollbarMode="showOnDemand" size="500,226" />
        </screen> """
        
SearchClient = """
        <screen name="ContextMenuScreen" position="325,163" size="500,400">
            <widget name="menu" position="0,207" scrollbarMode="showOnDemand" size="500,196"  />
            <widget name="search" position="57,13" size="424,69" foregroundColor="#e5b243" halign="center" font="Regular; 23" />
            <ePixmap name="search_pixmap" position="10,13" size="35,27" zPosition="0" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/search.png" />
            <widget name="infolist" position="10,90" size="471,112" />
        </screen> """
        
ChangelogScreen_SD = """
        <screen position="center,center" size="610,435" title="Info" >
            <widget name="changelog" position="0,0" size="610,435" font="Regular;18" transparent="1" foregroundColor="white" />
        </screen>"""
        
ChangelogScreen_HD = """
         <screen position="center,center" size="900,576" title="Info" >
            <widget name="changelog" position="0,0" size="900,576" font="Regular;18" transparent="1" foregroundColor="white" />
        </screen>"""
            

ShortcutsScreen_HD = """
        <screen position="center,center" size="900,576" title="ShortcutsScreen">
            <widget backgroundColor="#9f1313" font="Regular;20" halign="center" name="key_red" position="8,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#1f771f" font="Regular;20" halign="center" name="key_green" position="231,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#a08500" font="Regular;20" halign="center" name="key_yellow" position="454,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget backgroundColor="#18188b" font="Regular;20" halign="center" name="key_blue" position="677,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
            <widget name="menu" position="7,55" scrollbarMode="showOnDemand" size="885,445" transparent="1" />
        </screen>"""
     
ShortcutsScreen = """
        <screen position="center,center" size="610,435" title="Shortcuts" >
            <widget name="key_red" position="10,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="160,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="310,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="460,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <eLabel position="-1,55" size="612,1" backgroundColor="#999999" />
            <widget name="menu" position="0,55" size="610,350" scrollbarMode="showOnDemand" />
        </screen>"""
            
DownloadListScreen_HD = """
        <screen position="center,center" size="900,576" title="ShortcutsScreen">
          <widget backgroundColor="#9f1313" font="Regular;20" halign="center" name="key_red" position="8,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
          <widget backgroundColor="#1f771f" font="Regular;20" halign="center" name="key_green" position="231,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
          <widget backgroundColor="#a08500" font="Regular;20" halign="center" name="key_yellow" position="454,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
          <widget backgroundColor="#18188b" font="Regular;20" halign="center" name="key_blue" position="677,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
          <widget name="menu" position="7,55" scrollbarMode="showOnDemand" size="885,445" transparent="1" />
        </screen> """
            
DownloadListScreen = """
        <screen position="center,center" size="610,435" title="Main Menu" >
            <widget name="key_red" position="10,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="160,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="310,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="460,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="menu" position="0,55" size="610,350" scrollbarMode="showOnDemand" />
        </screen>"""

DownloadsScreen_HD = """
        <screen position="center,center" size="900,576" title="ShortcutsScreen">
          <widget backgroundColor="#9f1313" font="Regular;20" halign="center" name="key_red" position="8,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
          <widget backgroundColor="#1f771f" font="Regular;20" halign="center" name="key_green" position="231,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
          <widget backgroundColor="#a08500" font="Regular;20" halign="center" name="key_yellow" position="454,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
          <widget backgroundColor="#18188b" font="Regular;20" halign="center" name="key_blue" position="677,5" shadowColor="black" shadowOffset="-2,-2" size="215,45" valign="center" zPosition="1" />
          <widget name="menu" position="7,55" scrollbarMode="showOnDemand" size="885,445" transparent="1" />
        </screen> """

DownloadsScreen = """
        <screen position="center,center" size="610,435" title="Main Menu" >
            <widget name="key_red" position="10,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="160,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="310,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="460,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="menu" position="0,55" size="610,350" scrollbarMode="showOnDemand" />
        </screen>"""

        
DownloadStatusScreen = """
        <screen position="center,140" size="616,435">
            <widget name="filename" position="10,7" size="606,44" valign="top" font="Regular; 22" foregroundColor="red" halign="center" />
            <widget name="path_label" position="10,66" size="119,21" backgroundColor="background" font="Regular; 19" foregroundColor="#e5b243" />
            <widget name="path" position="10,66" size="606,41" valign="top" halign="left" font="Regular; 19" />
            <widget name="start_label" position="9,129" size="606,21" foregroundColor="#e5b243" font="Regular; 19" />
            <widget name="start" position="10,129" size="606,21" font="Regular; 19" />
            <widget name="finish_label" position="9,161" size="606,21" foregroundColor="#e5b243" font="Regular; 19" />
            <widget name="finish" position="10,161" size="606,21" font="Regular; 19" />
            <widget name="size_label" position="10,214" size="606,21" foregroundColor="#e5b243" font="Regular; 19" />
            <widget name="size" position="10,214" size="606,21" font="Regular; 19" />
            <widget name="speed_label" position="10,241" size="606,21" foregroundColor="#e5b243" font="Regular; 19" />
            <widget name="speed" position="10,241" size="606,21" font="Regular; 19" />
            <widget name="state_label" position="10,289" size="606,21" foregroundColor="#e5b243"  font="Regular; 19"/>
            <widget name="state" position="10,289" size="606,21" foregroundColors="#00b837,#ff2b39,#024dd9" font="Regular; 19"/>
            <widget name="status" position="10,330" size="606,89" font="Console; 14" />
        </screen>"""

CaptchaDialog_HD = """
        <screen name="CaptchaDialog" position="center,center" size="900,600" zPosition="99">
            <widget source="Title" render="Label" position=" 50,12" size="800, 33" halign="center" font="Regular;30" backgroundColor="background" shadowColor="black" shadowOffset="-3,-3" transparent="1"/>
            <eLabel position=" 20,55" size="860,1" backgroundColor="white"/>
            <widget name="captcha" position="450,65" zPosition="-1" size="175,70"  alphatest="on"/>
            <widget name="header" position="100,90" size="700,40" font="Regular;30" transparent="1" noWrap="1" />
            <widget name="text" position="100,164" size="700,50" font="Regular;46" transparent="1" noWrap="1" halign="right" valign="center"/>
            <widget name="list" position="20,272" size="860,225" selectionDisabled="1" transparent="1"/>
            <eLabel position="20,555" size="860,1" backgroundColor="white" />
        </screen>"""
        
CaptchaDialog_SD = """
        <screen name="CaptchaDialog" position="center,center" size="720,576" flags="wfNoBorder" zPosition="99">
            <widget source="Title" render="Label" position="10,12" size="720, 33" halign="center" font="Regular;30" backgroundColor="background" shadowColor="black" shadowOffset="-3,-3" transparent="1"/>
            <eLabel position=" 10,55" size="720,1" backgroundColor="white"/>
            <widget name="captcha" position="450,65" zPosition="1" size="175,70"  alphatest="on"/>
            <widget name="header" position="20,90" size="680,40" font="Regular;30" transparent="1" noWrap="1" />
            <widget name="text" position="20,160" size="680,50" font="Regular;46" transparent="1" noWrap="1" halign="right" valign="center"/>
            <widget name="list" position="20,272" size="680,225" selectionDisabled="1" transparent="1"/>
            <eLabel position="20,555" size="680,1" backgroundColor="white" />
        </screen>"""
        
Playlist = """
        <screen name="Playlist" position="center,center" size="650,450" flags="wfNoBorder" backgroundColor="#48080808">
            <widget name="menu" position="0,60" scrollbarMode="showOnDemand" size="650,390" backgroundColor="#48080808"/>
            <widget name="title" position="0,0" size="650,55" valign="center" halign="center" backgroundColor="#28080808" font="Regular; 24" foregroundColor="#e9b253" />
        </screen> """
        
ArchivCZSKMoviePlayer_HD = """
    <screen position="50,550" size="1180,130" title="InfoBar" backgroundColor="transparent" flags="wfNoBorder">
      <ePixmap position="0,0" size="1180,130" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/info_bg.png" />
      <ePixmap position="45,20" size="120,90" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/movie.png" alphatest="blend" />
      <eLabel position="180,10" size="2,110" backgroundColor="white" />
      <widget source="session.CurrentService" render="Label" position="202,11" size="710,30" font="Regular;28" backgroundColor="background" transparent="1">
            <convert type="ServiceName">Name</convert>
      </widget>
      <ePixmap position="215,58" size="677,16" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/prog_bg.png" zPosition="1" alphatest="on" />
      <widget name="buffer_slider" position="216,58" size="675,16" zPosition="2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/prog_buffer.png" transparent="1" />
      <widget source="session.CurrentService" render="Progress" position="216,58" size="675,16" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/prog.png" zPosition="3" transparent="1">
        <convert type="ServicePositionAdj">Position</convert>
      </widget>
      <widget source="session.CurrentService" render="PositionGauge" position="216,58" size="675,16" zPosition="4" transparent="1">
        <convert type="ServicePositionAdj">Gauge</convert>
      </widget>
      <widget source="session.CurrentService" render="Label" position="215,90" size="120,28" font="Regular;23" halign="left" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
        <convert type="ServicePositionAdj">Position,ShowHours</convert>
      </widget>
      <widget source="session.CurrentService" render="Label" position="335,90" size="435,28" font="Regular;23" halign="center" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
        <convert type="ServicePositionAdj">Length,ShowHours</convert>
      </widget>
      <widget source="session.CurrentService" render="Label" position="770,90" size="120,28" font="Regular;23" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
        <convert type="ServicePositionAdj">Remaining,Negate,ShowHours</convert>
      </widget>
      <eLabel position="930,10" size="2,110" backgroundColor="white" />
      <widget source="global.CurrentTime" render="Label" position=" 960,10" size="120,24" font="Regular;24" backgroundColor="#25080808" shadowColor="black" shadowOffset="-2,-2" transparent="1">
        <convert type="ClockToText">Format:%d.%m.%Y</convert>
      </widget>
      <widget source="global.CurrentTime" render="Label" position="1090,10" size=" 70,24" font="Regular;24" backgroundColor="#25080808" shadowColor="black" shadowOffset="-2,-2" transparent="1">
        <convert type="ClockToText">Default</convert>
      </widget>
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/ico_dolby_off.png" position="975,97" size="57,20" zPosition="1" alphatest="blend" />
      <widget source="session.CurrentService" render="Pixmap" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/ico_dolby_on.png" position="975,97" size="57,20" zPosition="2" alphatest="blend">
        <convert type="ServiceInfo">IsMultichannel</convert>
        <convert type="ConditionalShowHide" />
      </widget>
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/ico_format_off.png" position="1052,97" size="36,20" zPosition="1" alphatest="blend" />
      <widget source="session.CurrentService" render="Pixmap" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/ico_format_on.png" position="1052,97" size="36,20" zPosition="2" alphatest="blend">
        <convert type="ServiceInfo">IsWidescreen</convert>
        <convert type="ConditionalShowHide" />
      </widget>
      <widget source="session.CurrentService" render="Pixmap" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/ico_hd_off.png" position="1108,97" size="29,20" zPosition="1" alphatest="blend">
        <convert type="ServiceInfo">VideoWidth</convert>
        <convert type="ValueRange">0,720</convert>
        <convert type="ConditionalShowHide" />
      </widget>
      <widget source="session.CurrentService" render="Pixmap" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/gui/icon/mplayer/ico_hd_on.png" position="1108,97" size="29,20" zPosition="2" alphatest="blend">
        <convert type="ServiceInfo">VideoWidth</convert>
        <convert type="ValueRange">721,1980</convert>
        <convert type="ConditionalShowHide" />
      </widget>
      <widget name="buffer_label" position="960,40" size="120,20" text="Buffer" font="Regular; 16" backgroundColor="background" transparent="1"/>
      <widget name="buffer_state" position="1070,41" size="80,20" text="N/A" font="Regular; 16" backgroundColor="background" transparent="1" />
      <widget name="download_label" position="960,65" size="120,20" font="Regular; 16" backgroundColor="background" transparent="1"/>
      <widget name="download_speed" position="1070,65" size="80,20" text="N/A" font="Regular; 16" backgroundColor="background" transparent="1"/>
    </screen>
    """
