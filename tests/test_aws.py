from __future__ import (absolute_import, division, print_function)

from nose.tools import assert_equals
import yaml


from library.aws import DOCUMENTATION, EXAMPLES, RETURN


def test_documentation_yaml():
    print('Testing documentation YAML...')

    assert_equals(DOCUMENTATION.startswith(('---', '\n---')), True)

    assert_equals(EXAMPLES.startswith(('---', '\n---')), True)

    assert_equals(RETURN.startswith(('---', '\n---')), True)


def test_validate_yaml():

    documentation_yaml = yaml.load(DOCUMENTATION)

    example_yaml = yaml.load(EXAMPLES)

    return_yaml= yaml.load(RETURN)

    print(documentation_yaml['short_description'])

