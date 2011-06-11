from setuptools import setup, find_packages
setup(
    name = "Menagerie",
    version = "0.1",
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False,
    install_requires = ['pydot>=1.0.4', 'pyparsing', 'flask'],
    entry_points = { 'console_scripts': ['menagerie_console = menagerie.console:consoleMain', 
                                         'menagerie_app = menagerie.console:webappMain',
                                         'menagerie = menagerie.console:compileMain'] }
)
