
{ stdenvNoCC, fetchFromGitHub, lib }:

stdenvNoCC.mkDerivation {
  pname = "application-title-bar";
  version = "0.10.0";

  src = fetchFromGitHub {
    owner = "antroids";
    repo = "application-title-bar";
    rev = "v0.10.0";
    hash = "sha256-Zph+TwPXyf2r3PpJqWSdR0V9fFt2b2XWVfsAzuY3bP4=";
  };

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/plasma/plasmoids/com.github.antroids.application-title-bar

    cp -r package/. \
      $out/share/plasma/plasmoids/com.github.antroids.application-title-bar/

    runHook postInstall
  '';

  meta = {
    description = "KDE Plasma widget with window title and control buttons";
    homepage = "https://github.com/antroids/application-title-bar";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
}
