
{ stdenvNoCC, fetchFromGitLab, lib }:

stdenvNoCC.mkDerivation {
  pname = "thermal-monitor";
  version = "0.2.8";

  src = fetchFromGitLab {
    domain = "invent.kde.org";
    owner = "olib";
    repo = "thermalmonitor";
    rev = "v0.2.8";
    hash = "sha256-RxSy99zr6aObhjEWuWHFb7k6W0BvsLUj6fQCdn+n1Zw=";
  };

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/plasma/plasmoids/org.kde.olib.thermalmonitor

    cp -r package/. \
      $out/share/plasma/plasmoids/org.kde.olib.thermalmonitor/

    runHook postInstall
  '';

  meta = {
    description = "System temperature monitor for KDE Plasma";
    homepage = "https://invent.kde.org/olib/thermalmonitor";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
