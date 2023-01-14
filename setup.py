# coding=utf-8

########################################################################################################################

plugin_identifier = "psucontrol_servo"
plugin_package = "octoprint_psucontrol_servo"
plugin_name = "OctoPrint-PSUControl-Servo"
plugin_version = "1.0.0"
plugin_description = "TODO"
plugin_author = "Michael Wagner"
plugin_author_email = "octoprint_psucontrol_servo@michaeldwagner.dev"
plugin_url = "https://github.com/TheMDev/OctoPrint-PSUControl-Servo"
plugin_license = "AGPLv3"
plugin_requires = []
plugin_additional_data = []
plugin_additional_packages = []
plugin_ignored_packages = []
additional_setup_parameters = {"python_requires": ">=3,<4"}

########################################################################################################################

from setuptools import setup

try:
    import octoprint_setuptools
except:
    print(
        "Could not import OctoPrint's setuptools, are you sure you are running that under "
        "the same python installation that OctoPrint is installed under?"
    )
    import sys

    sys.exit(-1)

setup_parameters = octoprint_setuptools.create_plugin_setup_parameters(
    identifier=plugin_identifier,
    package=plugin_package,
    name=plugin_name,
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    mail=plugin_author_email,
    url=plugin_url,
    license=plugin_license,
    requires=plugin_requires,
    additional_packages=plugin_additional_packages,
    ignored_packages=plugin_ignored_packages,
    additional_data=plugin_additional_data,
)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge

    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

setup(**setup_parameters)
