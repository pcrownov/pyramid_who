##############################################################################
#
# Copyright (c) 2010 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################
import os

from zope.interface import implements

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated
from pyramid.security import Everyone
from repoze.who.config import make_api_factory_with_config

import logging;

log = logging.getLogger(__name__)

def _null_callback(identity, request):
    return ()

class WhoV2AuthenticationPolicy(object):
    implements(IAuthenticationPolicy)

    def __init__(self, config_file, identifier_id, callback=_null_callback):
        log.debug('__init__ : START')
        config_file = self._config_file = os.path.abspath(
                                          os.path.normpath(
                                          os.path.expandvars(
                                          os.path.expanduser(
                                            config_file))))
        conf_dir, _ = os.path.split(config_file)
        global_conf = {'here': conf_dir}
        self._api_factory = make_api_factory_with_config(global_conf,
                                                         config_file)
        self._identifier_id = identifier_id
        self._callback = callback

    def unauthenticated_userid(self, request):
        log.debug('unauthenticated_userid : START')
        identity = self._get_identity(request)
        log.debug('unauthenticated_userid : %s' % identity)
        if identity is not None:
            return identity['repoze.who.userid']

    def authenticated_userid(self, request):
        """ See IAuthenticationPolicy.
        """
        log.debug('authenticated_userid : START')
        identity = self._get_identity(request)

        log.debug('authenticated_userid : %s' % identity)
        if identity is not None:
            groups = self._callback(identity, request)
            if groups is not None:
                return identity['repoze.who.userid']

    def effective_principals(self, request):
        """ See IAuthenticationPolicy.
        """
        log.debug('effective_principals : START')
        identity = self._get_identity(request)
        log.debug('effective_principals : Identity : %s' % identity)
        groups = self._get_groups(identity, request)
        log.debug('effective_principals : Groups : %s' % groups)
        if len(groups) > 1:
            groups.insert(0, identity['repoze.who.userid'])
        return groups

    def remember(self, request, principal, **kw):
        """ See IAuthenticationPolicy.
        """
        log.debug('remember : START')
        api = self._getAPI(request)
        identity = {'repoze.who.userid': principal,
                    'identifier': api.name_registry[self._identifier_id],
                   }
        log.debug('remember : Identity : %s' % identity)
        return api.remember(identity)

    def forget(self, request):
        """ See IAuthenticationPolicy.
        """
        log.debug('forget : START')
        api = self._getAPI(request)
        identity = self._get_identity(request)
        log.debug('forget : Identity : %s' % identity)
        return api.forget(identity)

    def _getAPI(self, request):
        log.debug('_getAPI : START')
        return self._api_factory(request.environ)

    def _get_identity(self, request):
        log.debug("_get_identity : START")
        identity = request.environ.get('repoze.who.identity')
        log.debug("_get_identity : Identity : %s" % identity)
        if identity is None:
            api = self._getAPI(request)
            identity = api.authenticate()
        return identity

    def _get_groups(self, identity, request):
        log.debug("_get_groups : START")
        if identity is not None:
            dynamic = self._callback(identity, request)
            if dynamic is not None:
                groups = list(dynamic)
                groups.append(Authenticated)
                groups.append(Everyone)
                return groups
        return [Everyone]
