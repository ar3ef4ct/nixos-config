{
  description = "ArF's NixOS configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

    antigravity-nix = {
      url = "github:jacopone/antigravity-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    spicetify-nix = {
      url = "github:Gerg-L/spicetify-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    home-manager = {
      url = "github:nix-community/home-manager/release-25.11";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    plasma-manager = {
      url = "github:nix-community/plasma-manager";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };

    kwin-gestures = {
      url = "github:gbytedev/kwin-gestures";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, antigravity-nix, spicetify-nix, home-manager, plasma-manager, kwin-gestures, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      # ── System: sudo nixos-rebuild switch --flake ~/nixos-config#nixos ───────
      nixosConfigurations.nixos = nixpkgs.lib.nixosSystem {
        inherit system;
        specialArgs = { inherit antigravity-nix spicetify-nix kwin-gestures; };
        modules = [
          ./hosts/nixos

          # Home Manager
          home-manager.nixosModules.home-manager

          {
            home-manager = {
              useGlobalPkgs = true;
              useUserPackages = true;

              sharedModules = [
                plasma-manager.homeModules.plasma-manager
              ];

              users.arf = import ./home/arf;
            };
          }

          # Existing modules
          ./modules/desktop-kde.nix
          ./modules/web-lamp.nix
          ./modules/virtualization.nix
          ./modules/embedded.nix
          ./modules/remote.nix
          ./modules/gaming.nix
          ./modules/spicetify.nix
          ./modules/datascience.nix
          ./modules/mobile.nix

          ./users/arf.nix
        ];
      };

    };
}
