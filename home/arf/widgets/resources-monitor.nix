
{ stdenvNoCC, fetchFromGitHub, lib }:

stdenvNoCC.mkDerivation {
  pname = "resources-monitor";
  version = "3.5.0";

  src = fetchFromGitHub {
    owner = "orblazer";
    repo = "plasma-applet-resources-monitor";
    rev = "v3.5.0";
    hash = "sha256-86XT+qKGnaVxucDd4anBRaJXvD1li7Hv66bfaqJV7Z0=";
  };

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/plasma/plasmoids/org.kde.plasma.resources-monitor

    cp -r package/. \
      $out/share/plasma/plasmoids/org.kde.plasma.resources-monitor/

    runHook postInstall
  '';

  meta = {
    description = "KDE Plasma resource monitoring widget";
    homepage = "https://github.com/orblazer/plasma-applet-resources-monitor";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
}
