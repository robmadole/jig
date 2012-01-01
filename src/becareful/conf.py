from os.path import dirname, join
## BeCareful settings

# Name of the directory to create to hold BeCareful data
# This will be created in the root of the Git repository
BC_DIR_NAME = '.bc'

# Name of the file that will be created to manage a list of plugins and
# settings for them
BC_PLUGIN_CONFIG_FILENAME = 'plugins.cfg'
BC_PLUGIN_DIR = 'plugins'


## Plugin specific settings

# Each plugin has a configuration file, the name is
PLUGIN_CONFIG_FILENAME = 'config.cfg'

# Name of the script to run inside the plugin directory that represents
# the pre-commit script
PLUGIN_PRE_COMMIT_SCRIPT = 'pre-commit'

# Where can plugin pre-commit examples be found
PLUGIN_PRE_COMMIT_TEMPLATE_DIR = \
    join(dirname(__file__), 'data', 'pre-commits')
