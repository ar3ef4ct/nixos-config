{ ... }:

{
  imports = [
    ./appearance.nix
    ./kwin.nix
    ./shortcuts.nix
    ./widgets/panels.nix
  ];
  programs.plasma = {
    enable = true;
    workspace = {
      wallpaper = ./../../assets/ChengXiao.jpg;
      wallpaperFillMode = "preserveAspectCrop";
      };
  };
}
