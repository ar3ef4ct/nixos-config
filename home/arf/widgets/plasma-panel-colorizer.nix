
{ lib
, stdenv
, fetchFromGitHub
, cmake
, kdePackages
}:

stdenv.mkDerivation {
  pname = "plasma-panel-colorizer";
  version = "8.0.0";

  src = fetchFromGitHub {
    owner = "luisbocanegra";
    repo = "plasma-panel-colorizer";
    rev = "v8.0.0";
    hash = "sha256-SDmwfaP4Qc6OUrPWvzcu9VHNqPrqh9a2qqYk7Yejbkg=";
  };

  nativeBuildInputs = [
    cmake
    kdePackages.extra-cmake-modules
  ];

  buildInputs = [
    kdePackages.plasma-desktop
  ];

  strictDeps = true;

  cmakeFlags = [
    (lib.cmakeBool "INSTALL_PLASMOID" true)
    (lib.cmakeBool "BUILD_PLUGIN" true)
    (lib.cmakeFeature "Qt6_DIR" "${kdePackages.qtbase}/lib/cmake/Qt6")
  ];

  dontWrapQtApps = true;

  meta = {
    description = "Fully-featured KDE Plasma panel customization widget";
    homepage = "https://github.com/luisbocanegra/plasma-panel-colorizer";
    license = lib.licenses.gpl3Only;
    platforms = lib.platforms.linux;
  };
}
