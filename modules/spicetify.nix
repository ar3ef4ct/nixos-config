{ config, lib, pkgs, spicetify-nix, ... }:

let
  cfg = config.my.spicetify;
  spicePkgs = spicetify-nix.legacyPackages.${pkgs.stdenv.hostPlatform.system};
in
{
  imports = [ spicetify-nix.nixosModules.default ];

  options.my.spicetify.enable = lib.mkEnableOption "Spotify with Spicetify theme and extensions";

  config = lib.mkIf cfg.enable {
    programs.spicetify = {
      enable = true;
      theme = spicePkgs.themes.catppuccin;
      colorScheme = "mocha";
      enabledExtensions = with spicePkgs.extensions; [
        adblock
        hidePodcasts
        shuffle
      ];
    };
  };
}
