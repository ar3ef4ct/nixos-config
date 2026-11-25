{ config, lib, pkgs, ... }:

let
  cfg = config.my.gaming;
in
{
  options.my.gaming.enable = lib.mkEnableOption "Steam and gaming tools";

  config = lib.mkIf cfg.enable {
    programs = {
      steam = {
        enable = true;
        remotePlay.openFirewall = true;
        dedicatedServer.openFirewall = true;
      };
      gamemode.enable = true;
    };

    hardware.graphics = {
      enable = true;
      enable32Bit = true;
    };
  };
}
