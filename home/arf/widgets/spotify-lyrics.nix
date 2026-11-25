{ stdenvNoCC, fetchFromGitHub, lib }:

stdenvNoCC.mkDerivation {
  pname = "spotify-lyrics";
  version = "2.0.0";

  src = fetchFromGitHub {
    owner = "ocelotshark";
    repo = "plasmoid-spotify-lyrics";
    rev = "main";
    hash = "sha256-R7DA50jST8CTQASR/ZICwGX7xBXFGS3ItraNdUCw4x0=";
  };

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/plasma/plasmoids/com.github.ocelotshark.spotifylyrics

    cp -r src/. \
      $out/share/plasma/plasmoids/com.github.ocelotshark.spotifylyrics/

    runHook postInstall
  '';

  meta = {
    description = "Spotify lyrics widget for KDE Plasma";
    homepage = "https://github.com/ocelotshark/plasmoid-spotify-lyrics";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
