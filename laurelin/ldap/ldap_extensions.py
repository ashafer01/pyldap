"""Automatically generated by scripts/generate_extension_properties.py"""

from .extensible import Extensible


class LDAPExtensions(Extensible):

    @property
    def netgroups(self):
        """
        :rtype: laurelin.extensions.netgroups.LaurelinLDAPExtension
        """
        return self._get_extension_instance('netgroups')
