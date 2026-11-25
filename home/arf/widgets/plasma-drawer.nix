
{ stdenvNoCC, fetchFromGitHub, lib }:

stdenvNoCC.mkDerivation {
  pname = "plasma-drawer";
  version = "2.0.2";

  src = fetchFromGitHub {
    owner = "p-connor";
    repo = "plasma-drawer";
    rev = "v2.0.2";
    hash = "sha256-1RShJo74wS2Y98RyAlTozR0mcrF+3oKJ9yv7L/u1Uzo=";
  };

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/plasma/plasmoids/p-connor.plasma-drawer

    cp -r . $out/share/plasma/plasmoids/p-connor.plasma-drawer/

    runHook postInstall
  '';

  meta = {
    description = "Fullscreen customizable launcher for KDE Plasma";
    homepage = "https://github.com/p-connor/plasma-drawer";
    platforms = lib.platforms.linux;
  };
}
