import sys
from stat import S_IXUSR, S_IXGRP, S_IXOTH
from os import stat, chmod, makedirs
from os.path import isfile, isdir, join, realpath, dirname
from shutil import copytree

import sh

from jig.exc import (
    NotGitRepo, PreCommitExists, JigUserDirectoryError,
    GitTemplatesMissing, GitHomeTemplatesExists, GitConfigError,
    InitTemplateDirAlreadySet)
from jig.conf import JIG_DIR_NAME
from jig.gitutils.commands import git
from jig.gitutils.scripts import RUN_JIG_SCRIPT, AUTO_JIG_INIT_SCRIPT
from jig.gitutils.checks import is_git_repo

# Dependencies to make jig run
JIG_DIR = realpath(join(dirname(__file__), '..'))
SH_DIR = realpath(join(dirname(sh.__file__), '..'))


def _git_templates():
    """
    Search and return the location of the shared Git templates directory.

    :rtype: string or None
    """
    search_locations = [
        '/usr/share/git-core/templates',
        '/usr/local/share/git-core/templates',
        '/usr/local/git/share/git-core/templates'
    ]

    for possible_location in search_locations:
        if isdir(possible_location):
            return possible_location

    return None


def _pre_commit_has_hallmark(pre_commit_file):
    """
    Looks at a pre-commit file and determine if it was created by Jig.

    :returns: True if Jig created it
    """
    with open(pre_commit_file) as fh:
        script = fh.read()
        if u'from jig' in script or u'jig init' in script:
            return True
    return False


def _create_pre_commit(destination, template, context):
    """
    Writes a Git pre-commit hook from the template and make it executable.

    :param string destination: the filename of the pre-commit to create
    :param string template: the script template with replaceable vars
        compatible with string.format()
    :param dict context: keys and values to replace in the template
    :raises jig.exc.PreCommitExists: if there is already a Git hook for
        pre-commit present.
    """
    # Is there already a hook?
    if isfile(destination) and not _pre_commit_has_hallmark(destination):
        raise PreCommitExists('{0} already exists'.format(destination))

    with open(destination, 'w') as fh:
        fh.write(template.format(**context))

    sinfo = stat(destination)
    mode = sinfo.st_mode | S_IXUSR | S_IXGRP | S_IXOTH

    # Make sure it's executable
    chmod(destination, mode)

    return destination


def hook(gitdir):
    """
    Creates a pre-commit hook that runs Jig in normal mode.

    The hook will be configured to run using the version of Python that was
    used to install jig.

    Returns the full path to the newly created post-commit hook.

    :raises jig.exc.NotGitRepo: if the directory given is not a Git repository.
    """
    if not is_git_repo(gitdir):
        raise NotGitRepo('{0} is not a Git repository.'.format(
            gitdir))

    pc_filename = realpath(join(gitdir, '.git', 'hooks', 'pre-commit'))

    script_kwargs = {
        'python_executable': sys.executable,
        'jig_dir': JIG_DIR,
        'sh_dir': SH_DIR
    }

    return _create_pre_commit(pc_filename, RUN_JIG_SCRIPT, script_kwargs)


def create_auto_init_templates(user_home_directory):
    """
    Creates a Git templates directory with a Jig auto-init pre-commit hook.

    The templates directory will be created in the user's home directory inside
    a ~/.jig main directory.

    An attempt will be made to find the shared, global Git templates directory
    and copy it. An exception will be thrown if it cannot be found.

    :param string user_home_directory: Full path to the user's home directory
    """
    jig_user_directory = join(user_home_directory, JIG_DIR_NAME)
    jig_git_user_directory = join(jig_user_directory, 'git')

    try:
        map(makedirs, [jig_user_directory, jig_git_user_directory])
    except OSError as ose:
        if ose.errno == 13:
            # Permission denied
            raise JigUserDirectoryError(
                'Cannot create {0} Jig user directory'.format(
                    jig_user_directory
                )
            )
        if ose.errno != 17:
            # Some other kind of OSError
            raise JigUserDirectoryError(unicode(ose))

    # Copy the shared Git templates directory to .jig/git/templates
    git_templates_directory = _git_templates()

    if not git_templates_directory:
        raise GitTemplatesMissing()

    home_templates_directory = join(jig_git_user_directory, 'templates')

    if isdir(home_templates_directory):
        raise GitHomeTemplatesExists(home_templates_directory)

    copytree(git_templates_directory, home_templates_directory)

    pc_filename = realpath(
        join(home_templates_directory, 'hooks', 'pre-commit')
    )

    script_kwargs = {'python_executable': sys.executable}

    _create_pre_commit(
        pc_filename, AUTO_JIG_INIT_SCRIPT, script_kwargs
    )

    return home_templates_directory


def set_templates_directory(templates_directory):
    """
    Sets the template directory in the global Git config.
    """
    try:
        raw_config = git().config(
            '--global',
            '--list'
        )
    except git.error as e:
        raise GitConfigError(e)

    config = dict([i.split('=', 1) for i in raw_config.splitlines()])

    if 'init.templatedir' in config:
        raise InitTemplateDirAlreadySet(config['init.templatedir'])

    try:
        git().config(
            '--global',
            '--add',
            'init.templatedir',
            templates_directory
        )
    except git.error as e:
        raise GitConfigError(e)
