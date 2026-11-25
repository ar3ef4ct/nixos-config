
{ ... }:

{
  programs.plasma.shortcuts = {
    # Kwin
    kwin = {
      # Krohnkite
      KrohnkiteBTreeLayout = "Meta+U";
      KrohnkiteColumnsLayout = "Meta+Y";

      KrohnkiteFocusDown = "Meta+J";
      KrohnkiteFocusLeft = "Meta+H";
      KrohnkiteFocusRight = [ "Meta+L" "Meta+:" ];
      KrohnkiteFocusUp = "Meta+K";

      KrohnkiteGrowHeight = "Meta+Ctrl+J";
      KrohnkiteGrowWidth = "Meta+Ctrl+L";

      KrohnkiteDecrease = "Meta+O";
      KrohnkiteIncrease = "Meta+I";

      KrohnkiteMonocleLayout = "Meta+M";
      KrohnkiteNextLayout = "Meta+\\";
      KrohnkitePreviousLayout = "Meta+|";

      KrohnkiteSetMaster = "Meta+;";

      KrohnkiteShiftDown = "Meta+Shift+J";
      KrohnkiteShiftLeft = "Meta+Shift+H";
      KrohnkiteShiftRight = "Meta+Shift+L";
      KrohnkiteShiftUp = "Meta+Shift+K";

      KrohnkiteShrinkHeight = "Meta+Ctrl+K";
      KrohnkiteShrinkWidth = "Meta+Ctrl+H";

      KrohnkiteSpreadLayout = "Meta+G";

      KrohnkiteToggleFloat = "Meta+F";

      # Other Key
      "Activate Window Demanding Attention" = "Meta+Ctrl+A";
      "Edit Tiles" = "Meta+T";
      Expose = "Ctrl+F9";
      ExposeAll = [ "Ctrl+F10" "Launch (C)" ];
      ExposeClass = "Ctrl+F7";

      "Kill Window" = "Meta+Ctrl+Esc";
      MoveMouseToCenter = "Meta+F6";
      MoveMouseToFocus = "Meta+F5";
      Overview = "Meta+W";
      "Show Desktop" = "Meta+D";

      "Switch One Desktop Down" = "Meta+Ctrl+Down";
      "Switch One Desktop Up" = "Meta+Ctrl+Up";
      "Switch One Desktop to the Left" = "Meta+Ctrl+Left";
      "Switch One Desktop to the Right" = "Meta+Ctrl+Right";

      "Switch Window Down" = "Meta+Alt+Down";
      "Switch Window Left" = "Meta+Alt+Left";
      "Switch Window Right" = "Meta+Alt+Right";
      "Switch Window Up" = "Meta+Alt+Up";

      "Switch to Desktop 1" = "Ctrl+F1";
      "Switch to Desktop 2" = "Ctrl+F2";
      "Switch to Desktop 3" = "Ctrl+F3";
      "Switch to Desktop 4" = "Ctrl+F4";

      "Walk Through Windows" = [ "Meta+Tab" "Alt+Tab" ];
      "Walk Through Windows (Reverse)" = [
        "Meta+Shift+Tab"
        "Alt+Shift+Tab"
      ];

      "Window Close" = [ "Alt+F4" "Meta+Shift+W" ];
      "Window Maximize" = "Meta+PgUp";
      "Window Minimize" = "Meta+PgDown";

      "Window One Desktop Down" = "Meta+Ctrl+Shift+Down";
      "Window One Desktop Up" = "Meta+Ctrl+Shift+Up";
      "Window One Desktop to the Left" = "Meta+Ctrl+Shift+Left";
      "Window One Desktop to the Right" = "Meta+Ctrl+Shift+Right";

      "Window Operations Menu" = "Alt+F3";

      "Window Quick Tile Bottom" = "Meta+Down";
      "Window Quick Tile Left" = "Meta+Left";
      "Window Quick Tile Right" = "Meta+Right";
      "Window Quick Tile Top" = "Meta+Up";

      "Window to Next Screen" = "Meta+Shift+Right";
      "Window to Previous Screen" = "Meta+Shift+Left";
    };

    # Plasma Shell
    plasmashell = {
      "activate application launcher" = [ "Meta" "Alt+F1" ];

      "activate task manager entry 1" = "Meta+1";
      "activate task manager entry 2" = "Meta+2";
      "activate task manager entry 3" = "Meta+3";
      "activate task manager entry 4" = "Meta+4";
      "activate task manager entry 5" = "Meta+5";
      "activate task manager entry 6" = "Meta+6";
      "activate task manager entry 7" = "Meta+7";
      "activate task manager entry 8" = "Meta+8";
      "activate task manager entry 9" = "Meta+9";

      clipboard_action = "Meta+Ctrl+X";
      cycle-panels = "Meta+Alt+P";
      "previous activity" = "Meta+Shift+A";
      "show dashboard" = "Ctrl+F12";
      show-on-mouse-pos = "Meta+V";
      "switch to next activity" = "Meta+Q";
    };

    # Application launchers
    "services/firefox.desktop"._launch = "Meta+Shift+F";
    "services/org.kde.kate.desktop"._launch = "Meta+/";
    "services/org.kde.konsole.desktop"._launch = [
      "Ctrl+Alt+T"
      "Meta+'"
    ];
  };
}
