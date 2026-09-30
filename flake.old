{
  description = "Python 3.11 development environment";

  # Flake inputs
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  # Flake outputs
  outputs = { self, nixpkgs }:
    let
      # Systems supported
      allSystems = [
        "x86_64-linux" # 64-bit Intel/AMD Linux
        "aarch64-linux" # 64-bit ARM Linux
        "x86_64-darwin" # 64-bit Intel macOS
        "aarch64-darwin" # 64-bit ARM macOS
      ];

      # Helper to provide system-specific attributes
      forAllSystems = f: nixpkgs.lib.genAttrs allSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      # Development environment output
      devShells = forAllSystems ({ pkgs }: {
        default = pkgs.mkShell {
          # The Nix packages provided in the environment
          packages = with pkgs; [
            python312
            python312Packages.grpcio
            python312Packages.grpcio-tools
            #python312Packages.ipython
            #python312Packages.certifi
            #python312Packages.cryptography
            #python312Packages.rich
            #python312Packages.numpy
            #python312Packages.pandas
            #python312Packages.polars
            #python312Packages.psutil
            #python312Packages.pytest
            #python312Packages.poetry-core
            #python312Packages.loguru
            #python312Packages.requests
            #python312Packages.vulture
            uv
            ruff
            grpc-tools
            gcc
            openssl_3
            certstrap
          ];

          shellHook = ''

            if [ -z "$NIX_SHELL_NESTED" ]; then
              export NIX_SHELL_NESTED=1
              alias ipy="uv run ipython --nosep"
              export PS1="🧢 \e[38;5;211m\]g\e[38;5;111mBLP\[\e[0m $PS1"
              if [ ! -d .venv ]; then
                echo "Running uv init, adding ipython and pip"
                uv init .
                uv add pip
                uv add ipython
                uv add grpcio
                uv add grpcio-tools
              fi
              uv run pip list
            else
              echo "Nested nix-shell detected, skipping uv init"
            fi

          '';
        };
      });
    };
}


