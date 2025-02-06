# shell.nix
let
  # We pin to a specific nixpkgs commit for reproducibility.
  # Last updated: 2024-04-29. Check for new commits at https://status.nixos.org.
  pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/cf8cc1201be8bc71b7cbbbdaf349b22f4f99c7ae.tar.gz") {};
  database_src = (builtins.fetchGit {
    url = "git@github.com:C0D3-C0NJUR3R/qtrade_database.git";
    ref = "main";
    rev = "360041854ed07aa4894e96e7f00b4eb02da344a1";
    allRefs = false;
  });
  python = pkgs.python3.override {
    self = python;
    packageOverrides = pyfinal: pyprev: {
      alpaca-py = pyfinal.callPackage ./alpaca-py.nix { };
    };
  };
in pkgs.mkShell {
  packages = [
    (import "${database_src}/default.nix")
    (python.withPackages (python-pkgs: with python-pkgs; [
      # select Python packages here
      alembic
      pytest
      pip
      hypothesis

      pandas
      alpaca-py
      toolz
      sqlalchemy
      psycopg2 # required for postgres

    ]))
  ];
}