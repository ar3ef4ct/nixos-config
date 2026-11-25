{ config, lib, pkgs, ... }:

let
  cfg = config.my.mobile;

  platformVersions = [ "35" "36" ];

  buildToolsVersions = [ "35.0.0" "36.0.0" ];
  aapt2BuildTools = "35.0.0";

  ndkVersion = "27.0.12077973";

  cmakeVersion = "3.22.1";
  withEmulator = true;

  androidComposition = pkgs.androidenv.composeAndroidPackages {
    inherit platformVersions buildToolsVersions;
    includeNDK = true;
    ndkVersions = [ ndkVersion ];
    cmakeVersions = [ cmakeVersion ];
    includeEmulator = withEmulator;

    includeSystemImages = withEmulator;
    systemImageTypes = [ "google_apis" ];
    abiVersions = [ "x86_64" ];
  };

  androidSdk = androidComposition.androidsdk;
  sdkRoot = "${androidSdk}/libexec/android-sdk";
in
{
  options.my.mobile.enable = lib.mkEnableOption "Flutter and Android development";

  config = lib.mkIf cfg.enable {

    nixpkgs.config.android_sdk.accept_license = true;

    environment.systemPackages = [
      pkgs.flutter
      androidSdk
      pkgs.jdk17
      pkgs.android-studio
    ];

   environment.sessionVariables = {
      ANDROID_HOME = sdkRoot;
      ANDROID_SDK_ROOT = sdkRoot;
      JAVA_HOME = "${pkgs.jdk17}";

      GRADLE_OPTS = "-Dorg.gradle.project.android.aapt2FromMavenOverride=${sdkRoot}/build-tools/${aapt2BuildTools}/aapt2";
    };
  };
}
