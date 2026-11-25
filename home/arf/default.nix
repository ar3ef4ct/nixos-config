{ pkgs, ... }:

{
  home = {
    username = "arf";
    homeDirectory = "/home/arf";
    stateVersion = "25.11";
  };

  programs.home-manager.enable = true;

  imports = [
    ./plasma.nix
    ./packages.nix
  ];
}
