# shell.nix
let
  # We pin to a specific nixpkgs commit for reproducibility.
  # Last updated: 2025-02-06. Check for new commits at https://status.nixos.org.
  pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/030ba1976b7c0e1a67d9716b17308ccdab5b381e.tar.gz") {};
  database_src = (builtins.fetchGit {
    url = "git@github.com:C0D3-C0NJUR3R/qtrade_database.git";
    ref = "main";
    rev = "db1b6a00ab9f2dafa8efcb97f8a7dd8e2c628832";
    allRefs = false;
  });
  python = pkgs.python312.override {
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