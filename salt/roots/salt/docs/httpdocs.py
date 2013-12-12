#!/envs/docs/bin/python
# vim: set filetype=python :
import sys
import logging
import SimpleHTTPServer
import SocketServer
import posixpath
import argparse
import urllib
import os
from functools import partial

from sphinx.cmdline import main as sphinx_main
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format=' - %(message)s')

logger = logging.getLogger(__name__)


class BuildDocsHandler(FileSystemEventHandler):

    """
    On any change, rebuild the docs.

    """
    def __init__(self, build_func):
        self.build = build_func

    def on_any_event(self, event):
        self.build()


class DocsHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    """
    Request handler with an explicit root instead of using os.getcwd().

    """
    _root = None

    def translate_path(self, path):
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)

        # Use our root here instead of the current working directory
        path = self._root

        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path


def build_docs(source, destination, doctrees):
    """
    Use Sphinx to build the reStructuredText into HTML.
    """
    sphinx_argv = [
        '-b', 'html',
        '-d', doctrees,
        source,
        destination]

    sphinx_main(['sphinx-build'] + sphinx_argv)


def main(argv):
    """
    Build the docs and serve them with an HTTP server.
    """
    parser = argparse.ArgumentParser(description='Build and serve HTML Sphinx docs')

    parser.add_argument(
        '--port',
        help='Serve on this port, default 8000',
        type=int,
        default=8000)

    parser.add_argument(
        '--source',
        help='Directory of source Sphinx (reStructuredText) docs',
        type=os.path.realpath,
        default='docs/source')

    parser.add_argument(
        '--destination',
        help='Where to build the HTML output',
        type=os.path.realpath,
        default='docs/build/html')

    parser.add_argument(
        '--doctrees',
        help='Where the doctrees are built',
        type=os.path.realpath,
        default='docs/build/doctrees')

    options = parser.parse_args(argv)

    bound_build_docs = partial(build_docs, options.source, options.destination, options.doctrees)

    # Do the initial build
    bound_build_docs()

    # Watch the source directory for changes, build docs again if detected
    observer = Observer()
    observer.schedule(
        BuildDocsHandler(bound_build_docs),
        path=options.source, recursive=True)
    observer.start()

    # Set the root for the request handler, overriding Python stdlib current
    # working directory.
    DocsHTTPRequestHandler._root = options.destination

    server = SocketServer.TCPServer(
        ('', options.port),
        DocsHTTPRequestHandler)

    try:
        logger.info('Serving on localhost:{}'.format(options.port))
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        logger.info('(stopping server)')
        observer.stop()
    finally:
        observer.join()

    logging.info('Server stopped, exiting')
    sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
