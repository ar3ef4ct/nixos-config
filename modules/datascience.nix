{ config, lib, pkgs, ... }:

let
  cfg = config.my.datascience;
in
{
  options.my.datascience.enable = lib.mkEnableOption "Data science and Jupyter workspace";

  config = lib.mkIf cfg.enable {
    networking.firewall.allowedTCPPorts = [ 8888 ];

    environment.systemPackages = [
      (pkgs.python3.withPackages (ps: with ps; [
        jupyter
        jupyterlab
        notebook

        pandas
        numpy
        plotly

        seaborn
        matplotlib
        opencv4
        torch
        torchvision

        pillow
        scikit-learn
        lightgbm
        joblib
        streamlit
        openpyxl
      ]))
      pkgs.pandoc
    ];
  };
}
