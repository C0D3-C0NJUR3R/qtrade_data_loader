{ setuptools
, pkgs
, wheel
, alembic
, pytest
, hypothesis
, pandas
, toolz
, sqlalchemy
, psycopg2
, buildPythonPackage
}:
let
  python = pkgs.python312.override {
    self = python;
    packageOverrides = pyfinal: pyprev: {
      alpaca-py = pyfinal.callPackage ./alpaca-py.nix { };
    };
  };
in
buildPythonPackage {
  name = "databases";
  src = (builtins.fetchGit {
    url = "git@github.com:C0D3-C0NJUR3R/qtrade_database.git";
    ref = "main";
    rev = "34b2453cf747732322b6d4f84085da1b352889bb";
    allRefs = false;
  });
  pyproject = true;
  doCheck = true;
  propagatedBuildInputs = [
    (python.withPackages (python-pkgs: [
      setuptools
      wheel
      alembic
      pytest
      hypothesis
      pandas
      toolz
      sqlalchemy
      psycopg2
    ]))
  ];
}