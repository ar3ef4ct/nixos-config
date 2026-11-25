{ pkgs, ... }:

pkgs.writeShellScriptBin "nixconf" ''
  CONFIG_DIR="$HOME/nixos-config"
  FLAKE_TARGET="$CONFIG_DIR#nixos"

  show_help() {
      echo "Penggunaan: nixconf <perintah> [opsi]"
      echo ""
      echo "Perintah:"
      echo "  e, edit        Buka konfigurasi dengan Neovim ($CONFIG_DIR)"
      echo "  b, build       Build konfigurasi tanpa mengaktifkan (nixos-rebuild build)"
      echo "  switch         Build dan aktifkan konfigurasi (nixos-rebuild switch)"
      echo "  list           Tampilkan daftar generation NixOS"
      echo ""
      echo "Opsi:"
      echo "  --name <teks>  Tambahkan label pada versi generation"
  }

  if [[ $# -eq 0 ]]; then
      show_help
      exit 1
  fi

  COMMAND="$1"
  shift
  LABEL_NAME=""

  while [[ $# -gt 0 ]]; do
      case "$1" in
          --name)
              if [[ -n "$2" ]]; then
                  LABEL_NAME="''${2// /-}"
                  shift 2
              else
                  echo "Error: Parameter --name membutuhkan nilai teks."
                  exit 1
              fi
              ;;
          *)
              echo "Opsi tidak dikenal: $1"
              show_help
              exit 1
              ;;
      esac
  done

  case "$COMMAND" in
      e|edit)
          nvim "$CONFIG_DIR"
          ;;
      b|build)
          if [[ -n "$LABEL_NAME" ]]; then
              sudo NIXOS_LABEL="$LABEL_NAME" nixos-rebuild build --flake "$FLAKE_TARGET"
          else
              sudo nixos-rebuild build --flake "$FLAKE_TARGET"
          fi
          ;;
      switch)
          if [[ -n "$LABEL_NAME" ]]; then
              sudo NIXOS_LABEL="$LABEL_NAME" nixos-rebuild switch --flake "$FLAKE_TARGET"
          else
              sudo nixos-rebuild switch --flake "$FLAKE_TARGET"
          fi
          ;;
      list)
          nixos-rebuild list-generations
          ;;
      -h|--help|help)
          show_help
          ;;
      *)
          echo "Perintah tidak dikenal: $COMMAND"
          show_help
          exit 1
          ;;
  esac
''

