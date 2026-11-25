{ config, lib, pkgs, kwin-gestures, ... }:

let
  cfg = config.my.desktop;
in
{
  options.my.desktop.enable = lib.mkEnableOption "KDE Plasma 6 desktop";

  config = lib.mkIf cfg.enable {
    services = {
      xserver = {
        enable = true;
        xkb = {
          layout = "us";
          variant = "";
        };
        windowManager.icewm.enable = true;
      };
      displayManager.ly.enable = true;
      desktopManager.plasma6.enable = true;

      pulseaudio.enable = false;
      pipewire = {
        enable = true;
        alsa = {
          enable = true;
          support32Bit = true;
        };
        pulse.enable = true;
      };

      printing.enable = true;

      udisks2.enable = true;
    };

    security.rtkit.enable = true;
    security.pam.services.sddm.enableKwallet = true;

    hardware.graphics.enable = true;

    programs = {
      firefox.enable = true;
      appimage = {
        enable = true;
        binfmt = true;
      };
      kdeconnect.enable = true;
      partition-manager.enable = true;
    };

    fonts.packages = with pkgs; [
      noto-fonts
      noto-fonts-cjk-sans
      noto-fonts-color-emoji
      nerd-fonts.jetbrains-mono
      nerd-fonts.fira-code
      corefonts
    ];
  };
}
