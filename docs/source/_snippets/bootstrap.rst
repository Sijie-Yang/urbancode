::

   git clone --depth 1 https://github.com/Sijie-Yang/UrbanCode.git
   cd UrbanCode
   pip install -e ".[standard]"
   python -c "import urbancode as uc; print(uc.__version__); print(uc.backends.status())"

The Punggol pocket lives at ``examples/data/real/punggol`` inside this
repository. It is not inside the PyPI wheel. Run tutorial blocks from
the repository root so that path resolves. After install, probe extras
with :func:`urbancode.backends.status`.
