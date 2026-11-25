{ config, lib, pkgs, ... }:

let
  cfg = config.my.remote;
in
{
  options.my.remote.enable = lib.mkEnableOption "SSH and XRDP remote access";

  config = lib.mkIf cfg.enable {
    services = {
      openssh.enable = true;

      xrdp = {
        enable = true;
        openFirewall = true;
        defaultWindowManager = "dbus-run-session startplasma-x11";
      };
    };

    # Opens UDP 60000-61000 automatically
    programs.mosh.enable = true;

    programs.tmux = {
      enable = true;
      newSession = true;
      baseIndex = 1;
      historyLimit = 50000;
      escapeTime = 0;
      terminal = "screen-256color";
      extraConfig = ''
        set -g mouse on
      '';
    };

    environment.systemPackages = with pkgs; [
      dbus
      xorg.xauth
      xorg.xinit
      xorg.xorgserver
    ];
  };
}
