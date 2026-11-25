{ config, lib, pkgs, ... }:

let
  cfg = config.my.embedded;
in
{
  options.my.embedded.enable = lib.mkEnableOption "embedded / IoT development support";

  config = lib.mkIf cfg.enable {
    services.udev.extraRules = ''
      # Grant read/write access to Espressif ESP32-C3 built-in USB JTAG
      SUBSYSTEM=="usb", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", MODE="0666"
    '';

    # Serial port access
    users.users.arf = {
      extraGroups = [ "dialout" "uucp" ];
      packages = [ pkgs.arduino-ide ];
    };

    environment.systemPackages = [ pkgs.openocd ];
  };
}
