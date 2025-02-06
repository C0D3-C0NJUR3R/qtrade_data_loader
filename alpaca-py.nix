{
  buildPythonPackage,
  fetchPypi,
  setuptools,
  wheel,
  poetry-core,
  poetry-dynamic-versioning,
  msgpack,
  pandas,
  requests,
  pydantic,
  sseclient-py,
  websockets,
}:
buildPythonPackage rec {
  pname = "alpaca_py";
  version = "0.38.0";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-rPW0PBKDXsm81P4irdyvc1s4RHiRVVygTdXQy+G24yk=";
  };

  doCheck = true;

  # specific to buildPythonPackage, see its reference
  pyproject = true;
  propagatedBuildInputs = [
    setuptools
    poetry-dynamic-versioning
    poetry-core
    wheel
    msgpack
    pandas
    pydantic
    requests
    sseclient-py
    websockets
  ];
}
