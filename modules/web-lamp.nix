{ config, lib, pkgs, ... }:

let
  cfg = config.my.lamp;

  pythonWithPyQt = pkgs.python3.withPackages (ps: with ps; [ pyqt6 ]);

  nixamp-launcher = pkgs.writeScriptBin "nixamp-launcher" ''
    #!${pythonWithPyQt}/bin/python3
    ${builtins.readFile ../scripts/nixamp.py}
  '';
in
{
  options.my.lamp.enable = lib.mkEnableOption "Apache + MariaDB + PHP stack with NixAMP";

  config = lib.mkIf cfg.enable {
    services.mysql = {
      enable = true;
      package = pkgs.mariadb;
      settings.mysqld = {
      	port = 3306;
      };
    };

    # Apache HTTPD Server
    services.httpd = {
      enable = true;
      adminAddr = "arf@localhost";
      enablePHP = true;

      virtualHosts."localhost" = {
        documentRoot = "/var/www/localhost";

        extraConfig = ''
          <Directory "/var/www/localhost">
            AllowOverride All
            Require all granted
            DirectoryIndex index.php
          </Directory>

          <Directory "/var/www/localhost/phpmyadmin">
            AllowOverride All
            Require all granted
            DirectoryIndex index.php
          </Directory>

          RewriteEngine On
          RewriteCond /mnt/Windows_Host/Kuliah -d
          RewriteRule ^/kuliah(/.*)?$ /mnt/Windows_Host/Kuliah$1 [L]
          RewriteRule ^/kuliah(/.*)?$ /mnt/data/Kuliah$1 [L]

          <Directory "/mnt/Windows_Host/Kuliah">
            Options +Indexes
            AllowOverride All
            Require all granted
            DirectoryIndex kuliah.php index.php index.html
          </Directory>

          <Directory "/mnt/data/Kuliah">
            Options +Indexes
            AllowOverride All
            Require all granted
            DirectoryIndex kuliah.php index.php index.html
          </Directory>
        '';
      };
    };

    networking.firewall.allowedTCPPorts = [ 80 8080 ];

    environment.systemPackages = with pkgs; [
      php
      phpPackages.composer

      nodejs
      mariadb

      polkit_gnome

      nixamp-launcher
      (makeDesktopItem {
        name = "nixamp-control-panel";
        desktopName = "NixAMP";
        comment = "Control Panel for Apache and MariaDB";
        exec = "${nixamp-launcher}/bin/nixamp-launcher";
        terminal = false;
        categories = [ "System" "Development" ];
      })
    ];

    # Let user "arf" start/stop httpd and mysql without a password prompt
    security.polkit.extraConfig = ''
      polkit.addRule(function(action, subject) {
        if (action.id === "org.freedesktop.systemd1.manage-units") {
          if (action.lookup("unit") === "httpd.service" || action.lookup("unit") === "mysql.service") {
            if (subject.user === "arf") {
              return polkit.Result.YES;
            }
          }
        }
      });
    '';

    users.users.arf.extraGroups = [ config.services.httpd.group ];

    systemd.tmpfiles.rules = [
      "d /var/www/localhost 0775 ${config.services.httpd.user} ${config.services.httpd.group} -"
    ];
  };
}
