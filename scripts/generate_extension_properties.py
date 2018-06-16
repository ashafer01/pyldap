#!/usr/bin/env python3
import laurelin.ldap.schema  # hopefully can fix extension schema handling to not need this
from laurelin.ldap.extensible import ExtensionBase
from importlib import import_module
from inspect import stack
from os.path import dirname, abspath, join as path_join
import jinja2

EXTENSION_TEMPLATE = jinja2.Template('''"""Automatically generated by scripts/generate_extension_properties.py"""

from .extensible import ExtensionBase


class {{ EXTENDS }}Extensions(ExtensionBase):
{% for name, extinfo in AVAILABLE_EXTENSIONS %}
    @property
    def {{ name }}(self):
        """
        :rtype: {{ extinfo['module'] }}.Laurelin{{ EXTENDS }}Extension
        """
        return self._get_extension_instance('{{ name }}')
{% else %}
    pass
{% endfor %}
''')

BASE_DIR = path_join(dirname(abspath(stack()[0][1])), '..')


def main():
    ldap_extensions = {}
    ldapobject_extensions = {}

    files = [
        ('ldap_extensions.py', 'LDAP', ldap_extensions),
        ('ldapobject_extensions.py', 'LDAPObject', ldapobject_extensions),
    ]
    ext_classes = [
        ('LaurelinLDAPExtension', ldap_extensions),
        ('LaurelinLDAPObjectExtension', ldapobject_extensions),
    ]

    for name, extinfo in ExtensionBase.AVAILABLE_EXTENSIONS.items():
        mod = import_module(extinfo['module'])
        for classname, ext_dict in ext_classes:
            try:
                # ensure the required class exists in the module
                getattr(mod, classname)
                # if it does, store it in the appropriate dict
                ext_dict[name] = extinfo
            except AttributeError:
                # do nothing if it doesn't define the class
                pass

    for filename, extends_classname, available_extensions in files:
        # make a sorted list from the dict so we generate a deterministic file
        ext_names = list(available_extensions.keys())
        ext_names.sort()
        ext_list = []
        for name in ext_names:
            ext_list.append((name, available_extensions[name]))

        # render the template into a module
        with open(path_join(BASE_DIR, 'laurelin', 'ldap', filename), 'w') as f:
            f.write(EXTENSION_TEMPLATE.render(AVAILABLE_EXTENSIONS=ext_list, EXTENDS=extends_classname))


if __name__ == '__main__':
    main()
