# coding=utf-8
from jig.output import INFO


def _format_description(message):
    """
    Format the message body as the TAP Description.

    :param jig.output.Message message:
    """
    description = message.body

    if message.file:
        description = message.file

    if message.file and message.line:
        description = u'{file}:{line}'.format(
            file=message.file, line=message.line
        )

    if not description:
        return ''

    return ' - {0}'.format(description)


def _escape_for_yaml(body):
    """
    Performs YAML-compatible escaping on a string.

    :param str body: the string to escape
    """
    escaped_body = str(body).replace(u'\\', u'\\\\').replace(u'"', u'\\"')

    return u'"{0}"'.format(escaped_body)


def _format_message(test_number, message):
    """
    Format a single message suitable for TAP output.

    :param int test_number: the number of the test
    :param jig.output.Message message: the message to format
    :rtype: str
    :returns: the formatted message
    """
    preamble = u'ok' if message.type == INFO else u'not ok'
    plugin = message.plugin.name
    description = _format_description(message)
    body = message.body

    lines = []
    lines.append(u'{preamble} {test_number}{description}')
    lines.append(u'  ---')

    if message.file:
        lines.append(u'  message: {body}')

    lines.append(u'  plugin: {plugin}')
    lines.append(u'  severity: {type}')
    lines.append(u'  ...')

    return u'\n'.join(lines).format(
        preamble=preamble,
        test_number=test_number,
        description=description,
        body=_escape_for_yaml(body),
        plugin=plugin,
        type=message.type
    )


class TapFormatter(object):

    """
    Test Anything Protocol (TAP) formatter.

    """
    # Simple name used to specify this formatter on the command line
    name = 'tap'

    def print_results(self, printer, collator):
        """
        Format and print plugins results using TAP syntax.

        :param function printer: called to send output to the view
        :param ResultsCollator collator: access to the results
        """
        errors = collator.errors

        printer('TAP version 13')

        plan_sum = sum(collator.counts.values()) + len(errors)

        printer('1..{0}'.format(plan_sum))

        if plan_sum == 0:
            return

        cm, fm, lm = collator.messages

        messages = cm + fm + lm + errors

        for index in range(plan_sum):
            printer(_format_message(index + 1, messages[index]))
