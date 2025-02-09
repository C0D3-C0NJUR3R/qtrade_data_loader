{}:
with import <nixpkgs> {};
with pkgs.python312Packages;
let
  python = pkgs.python312.override {
    self = python;
    packageOverrides = pyfinal: pyprev: {
      qtrade_database = pyfinal.callPackage ./databases.nix { };
      alpaca-py = pyfinal.callPackage ./alpaca-py.nix { };
    };
  };

in
buildPythonApplication rec {
  pname = "fill_holes";
  version = "0.1.0";
  src = ./.;
  pyproject = true;
  doCheck = true;
  dontUnpack = true;
  preBuild = ''
cat > pyproject.toml << EOF
[project]
name = "fill_holes"
version = "0.0.1"
dependencies = [
  #"qtrade_database",
  "setuptools",
  "wheel",
  "alembic",
  "pytest",
  "hypothesis",
  "pandas",
  "toolz",
  "sqlalchemy",
  "psycopg2"
]

description = "Fill holes in the database"
readme = "README.md"
requires-python = ">=3.8"

[tool.setuptools.package-dir]
fill_holes = ""

[project.urls]
Homepage = "https://github.com/pypa/sampleproject"
Issues = "https://github.com/pypa/sampleproject/issues"
EOF
  '';
  propagatedBuildInputs = [
    (python.withPackages (python-pkgs: with python-pkgs; [
      setuptools
      qtrade_database
      alembic
      pytest
      alpaca-py
      requests
      msgpack
      numpy
      sseclient-py
      websockets
      pip
      hypothesis
      pydantic
      pandas
      toolz
      sqlalchemy
      psycopg2 # required for postgres
    ]))
  ];
  installPhase = ''
  install -Dm755 "${./${pname}.py}" "$out/bin/${pname}"
  install -Dm755 "${./data_util.py}" "$out/bin/data_util.py"
  '';
}