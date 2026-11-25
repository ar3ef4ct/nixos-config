{ ... }:

{
  programs.plasma.configFile = {
    "kwinrc" = {
      "Plugins" = {
        krohnkiteEnabled = true;
        karouselEnabled = false;
        blurEnabled = false;
        translucencyEnabled = true;
      };

      "Script-krohnkite" = {
        screenGapBetween = 4;
        screenGapBottom = 4;
        screenGapLeft = 4;
        screenGapRight = 4;
        screenGapTop = 17;
      };

      "Effect-translucency" = {
        Inactive = 79;
        IndividualMenuConfig = true;
        MoveResize = 100;
      };

      "Effect-blur" = {
        BlurStrength = 7;
        NoiseStrength = 13;
      };

      "Tiling" = {
        padding = 4;
      };

      "Windows" = {
        DelayFocusInterval = 200;
        RollOverDesktops = true;
      };

      "Xwayland" = {
        Scale = 1.1;
      };
    };
  };
}
