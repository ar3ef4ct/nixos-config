
{ ... }:

{
  programs.plasma = {
    configFile = {
      "kdeglobals" = {
        # ==========================================
        # GENERAL APPEARANCE
        # ==========================================
        "General" = {
          # Current color scheme is not explicitly identified.
          # Example: "BreezeDark"
          #
          # ColorScheme = "BreezeDark";

          # Font placeholders
          # Example: "Noto Sans,10,-1,5,50,0,0,0,0,0"
          #
          # font = "";
          # menuFont = "";
          # toolBarFont = "";
          # activeFont = "";
        };

        # ==========================================
        # KDE WORKSPACE
        # ==========================================
        "KDE" = {
          LookAndFeelPackage = "org.kde.breezedark.desktop";
          widgetStyle = "Breeze";

          # Cursor theme placeholder
          # Example: "breeze_cursors"
          #
          # cursorTheme = "";
        };

        # ==========================================
        # ICON THEME
        # ==========================================
        "Icons" = {
          # Example: "breeze-dark"
          #
          # Theme = "";
        };

        # ==========================================
        # WINDOW DECORATION
        # ==========================================
        "WM" = {
          # Future customization:
          # activeFont = "";
          # inactiveFont = "";
        };
      };
    };
  };
}
