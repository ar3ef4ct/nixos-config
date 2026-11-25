{ config, pkgs, lib, antigravity-nix, ... }:

{
  nixpkgs.overlays = [ antigravity-nix.overlays.default ];

  users.users.arf = {
    isNormalUser = true;
    description = "Arif Fakhrianto";
    extraGroups = [ "networkmanager" "wheel" ];

    packages = with pkgs; [
      # Gunakan variant IDE dari flake (sudah di-wrap FHS untuk mencegah crash agent)
      antigravity-nix.packages.${pkgs.system}.google-antigravity-ide
      antigravity-nix.packages.${pkgs.system}.google-antigravity-cli

      # Editors
      kdePackages.kate
      vscode
      nodejs

      # KDE / Plasma extras
      kdePackages.plasma-browser-integration
      kdePackages.kdeconnect-kde
      kdePackages.kdeplasma-addons
      kdePackages.kolourpaint
      kdePackages.plasma-workspace
      kdePackages.plasma-activities
      kdePackages.krdc
      kdePackages.kdialog
      kdePackages.isoimagewriter
      tesseract

      # Theming
      kdePackages.breeze-icons
      papirus-icon-theme
      bibata-cursors

      # Apps
      libreoffice
      anydesk
      discord-ptb
      gamescope
      qbittorrent
    ];
  };
}
