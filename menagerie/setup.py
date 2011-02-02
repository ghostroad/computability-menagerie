from setuptools import setup, find_packages
setup(
    name = "Menagerie",
    version = "0.1",
    packages = find_packages(),
    install_requires = ['pydot', 'pyparsing'],
    entry_points = { 'console_scripts': ['menagerie = menagerie.console:main'] }
)
