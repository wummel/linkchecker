# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2014 Bastian Kleineidam
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
Management of checking a queue of links with several threads.
"""
import os
import thread
import time
from .. import log, LOG_CHECK, LinkCheckerInterrupt, dummy, \
  fileutil, strformat, plugins
from ..cache import urlqueue, robots_txt, results
from . import aggregator, console


def visit_loginurl (aggregate):
    """Check for a login URL and visit it."""
    config = aggregate.config
    url = config["loginurl"]
    if not url:
        return
    if not fileutil.has_module("twill"):
        msg = strformat.format_feature_warning(module=u'twill',
            feature=u'login URL visit',
            url=u'http://twill.idyll.org/')
        log.warn(LOG_CHECK, msg)
        return
    from twill import commands as tc
    log.debug(LOG_CHECK, u"Visiting login URL %s", url)
    configure_twill(tc)
    tc.go(url)
    if tc.get_browser().get_code() != 200:
        log.warn(LOG_CHECK, _("Error visiting login URL %(url)s.") % \
          {"url": url})
        return
    submit_login_form(config, url, tc)
    if tc.get_browser().get_code() != 200:
        log.warn(LOG_CHECK, _("Error posting form at login URL %(url)s.") % \
          {"url": url})
        return
    #XXX store_cookies(tc.get_browser().cj, aggregate.cookies, url)
    resulturl = tc.get_browser().get_url()
    log.debug(LOG_CHECK, u"URL after POST is %s" % resulturl)
    # add result URL to check list
    from ..checker import get_url_from
    aggregate.urlqueue.put(get_url_from(resulturl, 0, aggregate))


def configure_twill (tc):
    """Configure twill to be used by LinkChecker.
    Note that there is no need to set a proxy since twill uses the same
    ones (provided from urllib) as LinkChecker does.
    """
    # make sure readonly controls are writeable (might be needed)
    tc.config("readonly_controls_writeable", True)
    # disable page refreshing
    tc.config("acknowledge_equiv_refresh", False)
    # fake IE 6.0 to talk sense into some sites (eg. SourceForge)
    tc.agent("Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0)")
    # tell twill to shut up
    tc.OUT = dummy.Dummy()
    from twill import browser
    browser.OUT = dummy.Dummy()
    # set debug level
    if log.is_debug(LOG_CHECK):
        tc.debug("http", 1)


def submit_login_form (config, url, tc):
    """Fill and submit login form."""
    user, password = config.get_user_password(url)
    cgiuser = config["loginuserfield"]
    cgipassword = config["loginpasswordfield"]
    formname = search_formname((cgiuser, cgipassword), tc)
    tc.formvalue(formname, cgiuser, user)
    tc.formvalue(formname, cgipassword, password)
    for key, value in config["loginextrafields"].items():
        tc.formvalue(formname, key, value)
    tc.submit()


def search_formname (fieldnames, tc):
    """Search form that has all given CGI fieldnames."""
    browser = tc.get_browser()
    for formcounter, form in enumerate(browser.get_all_forms()):
        for name in fieldnames:
            try:
                browser.get_form_field(form, name)
            except tc.TwillException:
                break
        else:
            return form.name or form.attrs.get('id') or formcounter
    # none found
    return None


def check_urls (aggregate):
    """Main check function; checks all configured URLs until interrupted
    with Ctrl-C.
    @return: None
    """
    try:
        visit_loginurl(aggregate)
    except Exception as msg:
        log.warn(LOG_CHECK, _("Error using login URL: %(msg)s.") % \
                 {'msg': str(msg)})
        raise
    try:
        aggregate.logger.start_log_output()
        if not aggregate.urlqueue.empty():
            aggregate.start_threads()
        check_url(aggregate)
        aggregate.finish()
        aggregate.end_log_output()
    except LinkCheckerInterrupt:
        raise
    except KeyboardInterrupt:
        interrupt(aggregate)
    except thread.error:
        log.warn(LOG_CHECK,
             _("Could not start a new thread. Check that the current user" \
               " is allowed to start new threads."))
        abort(aggregate)
    except Exception:
        # Catching "Exception" is intentionally done. This saves the program
        # from libraries that raise all kinds of strange exceptions.
        console.internal_error()
        aggregate.logger.log_internal_error()
        abort(aggregate)
    # Not catched exceptions at this point are SystemExit and GeneratorExit,
    # and both should be handled by the calling layer.


def check_url (aggregate):
    """Helper function waiting for URL queue."""
    while True:
        try:
            aggregate.urlqueue.join(timeout=30)
            break
        except urlqueue.Timeout:
            # Cleanup threads every 30 seconds
            aggregate.remove_stopped_threads()
            if not any(aggregate.get_check_threads()):
                break


def interrupt (aggregate):
    """Interrupt execution and shutdown, ignoring any subsequent
    interrupts."""
    while True:
        try:
            log.warn(LOG_CHECK,
               _("user interrupt; waiting for active threads to finish"))
            log.warn(LOG_CHECK,
               _("another interrupt will exit immediately"))
            abort(aggregate)
            break
        except KeyboardInterrupt:
            pass


def abort (aggregate):
    """Helper function to ensure a clean shutdown."""
    while True:
        try:
            aggregate.abort()
            aggregate.finish()
            aggregate.end_log_output()
            break
        except KeyboardInterrupt:
            log.warn(LOG_CHECK, _("user abort; force shutdown"))
            aggregate.end_log_output()
            abort_now()


def abort_now ():
    """Force exit of current process without cleanup."""
    if os.name == 'posix':
        # Unix systems can use signals
        import signal
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGKILL)
    elif os.name == 'nt':
        # NT has os.abort()
        os.abort()
    else:
        # All other systems have os._exit() as best shot.
        os._exit(3)


def get_aggregate (config):
    """Get an aggregator instance with given configuration."""
    _urlqueue = urlqueue.UrlQueue(max_allowed_urls=config["maxnumurls"])
    _robots_txt = robots_txt.RobotsTxt()
    plugin_manager = plugins.PluginManager(config)
    result_cache = results.ResultCache()
    return aggregator.Aggregate(config, _urlqueue, _robots_txt, plugin_manager,
        result_cache)
