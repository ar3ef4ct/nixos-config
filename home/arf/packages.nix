{ pkgs, ... }:

let
  resourcesMonitor = pkgs.callPackage
    ./widgets/resources-monitor.nix
    {};

  plasmaDrawer = pkgs.callPackage
    ./widgets/plasma-drawer.nix
    {};

  thermalMonitor = pkgs.callPackage
    ./widgets/thermal-monitor.nix
    {};

  spotifyLyrics = pkgs.callPackage
    ./widgets/spotify-lyrics.nix
    {};
in
{
  home.packages = [
    # KWin
    pkgs.kdePackages.krohnkite

    # Plasma Widgets
    pkgs.kara
    resourcesMonitor
    plasmaDrawer
    thermalMonitor
    spotifyLyrics

    # Widget dependencies
    pkgs.kdePackages.ksystemstats
    pkgs.lm_sensors
    pkgs.cava
  ];
}
