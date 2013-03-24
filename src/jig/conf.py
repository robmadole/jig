from os.path import dirname, join
from datetime import timedelta

## General settings

# What codec to use when dealing with unicode conversion
CODEC = 'utf8'


## jig settings

# Name of the directory to create to hold jig data
# This will be created in the root of the Git repository
JIG_DIR_NAME = '.jig'

# Name of the file that will be created to manage a list of plugins and
# settings for them
JIG_PLUGIN_CONFIG_FILENAME = 'plugins.cfg'
JIG_PLUGIN_DIR = 'plugins'


## Plugin specific settings

# Each plugin has a configuration file, the name is
PLUGIN_CONFIG_FILENAME = 'config.cfg'

# Name of the script to run inside the plugin directory that represents
# the pre-commit script
PLUGIN_PRE_COMMIT_SCRIPT = 'pre-commit'

# Where can plugin pre-commit examples be found
PLUGIN_PRE_COMMIT_TEMPLATE_DIR = \
    join(dirname(__file__), 'data', 'pre-commits')

# How often to check for plugin updates
PLUGIN_CHECK_FOR_UPDATES = timedelta(days=5)

# The directory inside of the plugins directory that contains tests
PLUGIN_TESTS_DIRECTORY = 'tests'

# Name of the file that serves as both documentation and tests for a plugin
PLUGIN_EXPECTATIONS_FILENAME = 'expect.rst'
