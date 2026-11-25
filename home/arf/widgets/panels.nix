
{ ... }:

{
  programs.plasma.panels = [
    {
      location = "top";
      height = 34;
      floating = true;

      widgets = [
        # 1. Plasma Drawer
        {
          name = "p-connor.plasma-drawer";
          config.General = {
            backgroundOpacity = 75;
            customButtonImage = "nix-snowflake";
            useCustomButtonImage = true;
            searchRunners = "krunner_services,krunner_systemsettings,krunner_recentdocuments,baloosearch,krunner_placesrunner,locations,krunner_bookmarksrunner,krunner_appstream,calculator,krunner_shell";
          };
        }

        # 2. Separator
        "org.kde.plasma.marginsseparator"

        # 3. Thermal Monitor
        {
          name = "org.kde.olib.thermalmonitor";
          config.General.sensors = builtins.toJSON [
            {
              name = "Average CPU Temperature";
              sensorId = "cpu/all/averageTemperature";
            }
          ];
        }

        # 4. Resources Monitor
        {
          name = "org.kde.plasma.resources-monitor";
          config = {
            Appearance = {
              abbreviate = true;
              autoFontAndSize = false;
              displayment = "hover";
              fillPanel = true;
              fontFamily = "Noto Sans";
              fontSize = 6;
              fontStyleName = "Regular";
              fontWeight = 400;
              graphFillOpacity = 36;
              graphSpacing = 3;
              keepFontSize = true;
              placement = "top-left";
            };

            General.graphs = builtins.toJSON [
              {
                _v = 4;
                type = "cpu";
                sizes = [ 20 20 ];
                colors = [ "highlightColor" "textColor" "textColor" ];
                sensorsType = [ "usage" "none" false ];
                clockAggregator = "average";
                eCoresCount = 0;
                thresholds = [ 85 105 ];
                fontSize = -1;
              }
              {
                _v = 4;
                type = "memory";
                sizes = [ 20 20 ];
                colors = [ "highlightColor" "negativeTextColor" ];
                sensorsType = [ "physical" "none" ];
                thresholds = [ 70 90 ];
                fontSize = -1;
              }
            ];
          };
        }

        # 5. Separator
        "org.kde.plasma.marginsseparator"

        # 6. Spotify Lyrics
        {
          name = "com.github.ocelotshark.spotifylyrics";
          config.General = {
            artBorderEffect = "progress";
            artBorderWidth = 1;
            artCornerRadius = 28;
            infoAlignment = "center";
            infoGap = 9;
            infoOverflow = "scroll";
            infoVerticalAlignment = "center";
            infoWidth = 100;
            lyricsBrightness = 25;
            lyricsEffect = "typewriter";
            lyricsFontSize = 13;
            lyricsGap = 11;
            lyricsInactiveColorMode = "custom";
            lyricsInactiveOpacity = 0;
            lyricsOffsetMs = 200;
            lyricsWidth = 500;
            showArtist = false;
            showLyricsStatus = true;
            showProgressBar = true;
            titleBrightness = 100;
            titleFontFamily = "Noto Sans";
            titleFontSize = 10;
          };
        }

        # 7. Expanding spacer
        {
          panelSpacer = {
            expanding = true;
          };
        }

        # 8. Digital Clock
        {
          name = "org.kde.plasma.digitalclock";
          config.Appearance = {
            autoFontAndSize = false;
            customDateFormat = "dddd, dd MMM yyyy";
            dateFormat = "custom";
            fontFamily = "Noto Sans";
            fontStyleName = "Regular";
            fontWeight = 400;
            showSeconds = "Never";
            use24hFormat = 2;
          };
        }

        # 9. Expanding spacer
        {
          panelSpacer = {
            expanding = true;
          };
        }

        # 10. Activity Bar
        "org.kde.plasma.activitybar"

        # 11. Kara
        {
          name = "org.dhruv8sh.kara";
          config = {
            appearance.txtColor = "227,7,7";

            general = {
              highlightType = 2;
              wrapOn = false;
            };

            type1.t1width = 30;
            type4.labelsList = "1\n2";
          };
        }

        # 12. System Tray
        {
          systemTray = {
            items = {
              showAll = false;

              extra = [
                "org.kde.plasma.addons.katesessions"
                "org.kde.plasma.volume"
                "org.kde.plasma.brightness"
                "org.kde.plasma.cameraindicator"
                "org.kde.plasma.devicenotifier"
                "org.kde.kscreen"
                "org.kde.kdeconnect"
                "org.kde.plasma.keyboardlayout"
                "org.kde.plasma.keyboardindicator"
                "org.kde.plasma.battery"
                "org.kde.plasma.networkmanagement"
                "org.kde.plasma.printmanager"
                "org.kde.plasma.clipboard"
                "org.kde.plasma.manage-inputmethod"
                "org.kde.plasma.diskquota"
                "org.kde.plasma.mediacontroller"
                "org.kde.plasma.notifications"
                "org.kde.plasma.trash"
                "org.kde.plasma.weather"
              ];

              hidden = [
                "org.kde.plasma.addons.katesessions"
                "org.kde.plasma.brightness"
                "org.kde.plasma.cameraindicator"
                "org.kde.plasma.devicenotifier"
                "org.kde.kscreen"
                "org.kde.kdeconnect"
                "org.kde.plasma.keyboardlayout"
                "org.kde.plasma.keyboardindicator"
                "org.kde.plasma.printmanager"
                "org.kde.plasma.clipboard"
                "org.kde.plasma.manage-inputmethod"
                "org.kde.plasma.diskquota"
                "org.kde.plasma.mediacontroller"
                "org.kde.plasma.notifications"
                "org.kde.plasma.trash"
                "org.kde.plasma.weather"
                "spotify-client"
              ];

              shown = [
                "org.kde.plasma.volume"
                "org.kde.plasma.battery"
                "org.kde.plasma.networkmanagement"
              ];
            };
          };
        }

        # 13. Sticky Notes
        "org.kde.plasma.notes"

        {
          plasmaPanelColorizer = {
            general = {
              enable = true;
              hideWidget = true;
            };

            presetAutoLoading.normal = "Dock";
          };
        }

        # 15. Separator
        "org.kde.plasma.marginsseparator"

        # 16. Window List
        {
          name = "org.kde.plasma.windowlist";
          config.General.showText = false;
        }

        # 17. Application Title Bar
        {
          applicationTitleBar = {
            settings = {
              Appearance = {
                widgetButtonsAnimation = 95;
                widgetButtonsAspectRatio = 85;
                widgetElements = "windowTitle,spacer,windowMinimizeButton,windowMaximizeButton,windowCloseButton";
                widgetMargins = 0;
                widgetSpacing = 5;
                widgetToolTipMode = "Disabled";
                windowTitleFontBold = false;
                windowTitleFontSize = 9;
                windowTitleMaximumWidth = 180;
                windowTitleMinimumWidth = 180;
                windowTitleUndefined = "KDE in NixOS";
              };

              Behavior = {
                disableButtonsForNotHoveredWidget = true;
                widgetMouseAreaMiddleClickAction = "Window Move";
                widgetMouseAreaMiddleDoubleClickAction = "Window to Next Desktop";
                widgetMouseAreaMiddleLongPressAction = "Window Resize";
                widgetMouseAreaWheelDownAction = "Walk Through Windows (Reverse)";
                widgetMouseAreaWheelUpAction = "Walk Through Windows";
              };
            };
          };
        }
      ];
    }
  ];
}
