# -*- coding: iso-8859-1 -*-
# Copyright (C) 2014 Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Module for plugin management.
"""
from .. import loader, log, LOG_PLUGIN
from ..decorators import notimplemented


class _PluginBase(object):
    """Basic plugin class featuring plugin identification and
    helper functions."""

    def __init__(self, config):
        """Add plugin-specific configuration."""
        pass

    @notimplemented
    def applies_to(self, url_data, **kwargs):
        """See if url_data should be handled by this plugin."""
        pass

    @notimplemented
    def check(self, url_data):
        """Common check method run for all plugins."""
        pass

    @classmethod
    def read_config(cls, configparser):
        """Read configuration file options."""
        pass


class _ConnectionPlugin(_PluginBase):
    """Plugins run after connection checks."""
    pass


class _ContentPlugin(_PluginBase):
    """Plugins run for valid URLs with content."""
    pass


class _ParserPlugin(_PluginBase):
    """Plugins run for valid URLs to parse their contents."""
    pass


def get_plugin_modules(folders, package='plugins',
                       parentpackage='linkcheck.dummy'):
    """Get plugin modules for given folders."""
    for folder in folders:
        for module in loader.get_folder_modules(folder, parentpackage):
            yield module
    for module in loader.get_package_modules(package):
        yield module


def get_plugin_classes(modules):
    """Get plugin classes for given modules."""
    classes = (_ConnectionPlugin, _ContentPlugin, _ParserPlugin)
    return loader.get_plugins(modules, classes)


class PluginManager(object):
    """Manage all connection and content plugins."""

    def __init__(self, config):
        """Load enabled plugins."""
        self.connection_plugins = []
        self.content_plugins = []
        self.parser_plugins = []
        folders = config["pluginfolders"]
        modules = get_plugin_modules(folders)
        self.load_modules(modules, config)

    def load_modules(self, modules, config):
        """Load plugin modules."""
        for pluginclass in get_plugin_classes(modules):
            name = pluginclass.__name__
            if name in config["enabledplugins"]:
                if issubclass(pluginclass, _ConnectionPlugin):
                    log.debug(LOG_PLUGIN, "Enable connection plugin %s", name)
                    self.connection_plugins.append(pluginclass(config[name]))
                elif issubclass(pluginclass, _ContentPlugin):
                    log.debug(LOG_PLUGIN, "Enable content plugin %s", name)
                    self.content_plugins.append(pluginclass(config[name]))
                elif issubclass(pluginclass, _ParserPlugin):
                    log.debug(LOG_PLUGIN, "Enable parser plugin %s", name)
                    self.parser_plugins.append(pluginclass(config[name]))
                else:
                    raise ValueError("Invalid plugin class %s" % pluginclass)

    def run_connection_plugins(self, url_data):
        """Run all connection plugins."""
        run_plugins(self.connection_plugins, url_data)

    def run_content_plugins(self, url_data):
        """Run all content plugins."""
        run_plugins(self.content_plugins, url_data)

    def run_parser_plugins(self, url_data, pagetype):
        """Run parser plugins for given pagetype."""
        run_plugins(self.parser_plugins, url_data, stop_after_match=True, pagetype=pagetype)


def run_plugins(plugins, url_data, stop_after_match=False, **kwargs):
    """Run the check(url_data) method of given plugins."""
    for plugin in plugins:
        log.debug(LOG_PLUGIN, "Run plugin %s", plugin.__class__.__name__)
        if plugin.applies_to(url_data, **kwargs):
            plugin.check(url_data)
            if stop_after_match:
                break
