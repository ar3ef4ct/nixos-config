{ config, lib, pkgs, ... }:

let
  nixconf = pkgs.callPackage ../../scripts/nixconf.nix { };
in
{
  imports = [
    ./hardware-configuration.nix
  ];

  my = {
    desktop.enable = true;        # KDE Plasma 6, audio, printing, fonts
    lamp.enable = true;           # Apache + MariaDB + PHP + NixAMP
    virtualization.enable = true; # libvirt/QEMU, virt-manager, spice
    embedded.enable = true;       # ESP32 udev, openocd, serial groups
    remote.enable = true;         # SSH + XRDP
    gaming.enable = true;         # Steam, gamemode
    spicetify.enable = true;      #
    datascience.enable = true;
    mobile.enable = true;
  };



  boot = {
    loader = {
      systemd-boot.enable = false;
      grub = {
        enable = true;
        efiSupport = true;
        device = "nodev";
        efiInstallAsRemovable = false;
        useOSProber = true;
     };
      efi = {
        canTouchEfiVariables = true;
        efiSysMountPoint = "/boot";
      };
    };
    kernelParams = [
      "zswap.enabled=1"
      "zswap.compressor=zstd"
      "zswap.max_pool_percent=20"
      "zswap.shrinker_enabled=1"
    ];
  };

  time.timeZone = "Asia/Jakarta";
  i18n.defaultLocale = "en_US.UTF-8";

  networking = {
    hostName = "nixos";
    networkmanager = {
      enable = true;
      wifi.macAddress = "preserve";
    };
  };

  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  nixpkgs.config.allowUnfree = true;

  programs = {
    direnv = {
      enable = true;
      nix-direnv.enable = true;
    };
    tmux = {
      enable = true;
      plugins = with pkgs.tmuxPlugins; [
        resurrect
        continuum
      ];
      extraConfig = ''
        set -g @resurrect-capture-pane-contents 'on'
        set -g @resurrect-strategy-vim 'session'
        set -g @resurrect-strategy-nvim 'session'

        set -g @resurrect-hook-post-save-all 'target=$(readlink -f ~/.tmux/resurrect/last); sed "s| --cmd .*-vim-pack-dir||g; s|/etc/profiles/per-user/$USER/bin/||g; s|/nix/store/[^/]*/bin/||g" "$target" > "$target.tmp" && mv "$target.tmp" "$target"'

        set -g @continuum-restore 'on'
        set -g @continuum-save-interval '15'
      '';
    };
    bash.interactiveShellInit = ''
      sudo() {
        if [ "$1" = "nixos-rebuild" ] && [ "$2" = "switch" ]; then
          local has_flake=0 a
          for a in "$@"; do
            case "$a" in
              --flake|--flake=*) has_flake=1 ;;
            esac
          done

          if [ "$has_flake" = 0 ]; then
            echo "WARNING: no --flake given, so this rebuilds from /etc/nixos, not ~/nixos-config."
            read -r -p 'Type "Yes, from /etc/nixos" to continue: ' answer
            if [ "$answer" != "Yes, from /etc/nixos" ]; then
              echo "Cancelled."
              return 1
            fi
          fi
        fi
        command sudo "$@"
      }
    '';
    nix-ld = {
      enable = true;
      libraries = with pkgs; [
        libusb1
        hidapi
        stdenv.cc.cc
        zlib
        glibc
        openssl
        curl
        util-linux
        icu
        libxml2
        glib
      ];
    };
  };

  security.polkit.enable = true;

  environment.sessionVariables = {
    EDITOR = "nvim";
    VISUAL = "nvim";
  };

environment.systemPackages = with pkgs; [
  # Custom scripts
  nixconf

  # System utilities
  wget
  curl
  fbv
  btop
  git
  neofetch
  procps
  psmisc
  lm_sensors
  ntfs3g
  feh
  ripgrep

  # Development tools
  gcc
  gnumake
  cmake
  ninja
  pkg-config
  gdb
  valgrind

  # ipy-edit dependencies
  jansson
  ncurses
  zeromq
  wl-clipboard

  # Editor
  neovim
];

  system.stateVersion = "25.11";
}
