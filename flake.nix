{
  description = "Python 3.11 development environment";

  # Flake inputs
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs"; # also valid: "nixpkgs"
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
            python312Packages.ipython
            python312Packages.colorama
            python312Packages.certifi
            python312Packages.cryptography
            python312Packages.rich
            grpc-tools
            openssl_3_3
            certstrap
          ];
          shellHook = ''
            alias ipy="ipython --nosep"
            export PS1="🧢 \e[38;5;211m\]g\e[38;5;111mBLP\[\e[0m $PS1";
          '';
        };
      });
    };
}


