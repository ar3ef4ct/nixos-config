{ config, lib, pkgs, ... }:

let
  cfg = config.my.virtualization;
in
{
  options.my.virtualization.enable = lib.mkEnableOption "libvirt/QEMU virtualization";

  config = lib.mkIf cfg.enable {
    virtualisation = {
      libvirtd = {
        enable = true;
        qemu = {
          package = pkgs.qemu_kvm;
          runAsRoot = true;
          swtpm.enable = true;
          vhostUserPackages = [ pkgs.virtiofsd pkgs.spice-gtk ];
        };
      };
      hypervGuest = {
        enable = true;
      };
      spiceUSBRedirection.enable = true;
    };

    programs.virt-manager.enable = true;

    services = {
      spice-vdagentd.enable = true;

      dnsmasq = {
        enable = true;
        settings = {
          bind-dynamic = true;
          except-interface = [ "virbr0" "wlp2s0" ];
        };
      };
    };

    boot.kernel.sysctl."net.ipv4.ip_forward" = 1;
    networking.firewall.trustedInterfaces = [ "virbr0" ];

    users.users.arf.extraGroups = [ "libvirtd" ];

    environment.systemPackages = with pkgs; [
      spice-gtk
      virt-viewer
      usbredir
      cifs-utils
    ];
  };
}
