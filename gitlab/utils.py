# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2017 Gauvain Pocentek <gauvain@pocentek.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import functools
from inspect import getmembers, isfunction
from urllib.parse import urlparse


class _StdoutStream(object):
    def __call__(self, chunk):
        print(chunk)


async def aresponse_content(response, streamed, action):
    response = await response
    if streamed is False:
        return response.content

    if action is None:
        action = _StdoutStream()

    async for chunk in response.aiter_bytes():
        if chunk:
            action(chunk)


def response_content(response, streamed, action):
    if asyncio.iscoroutine(response):
        return aresponse_content(response, streamed, action)

    if streamed is False:
        return response.content

    if action is None:
        action = _StdoutStream()

    for chunk in response.iter_bytes():
        if chunk:
            action(chunk)


def copy_dict(dest, src):
    for k, v in src.items():
        if isinstance(v, dict):
            # Transform dict values to new attributes. For example:
            # custom_attributes: {'foo', 'bar'} =>
            #   "custom_attributes['foo']": "bar"
            for dict_k, dict_v in v.items():
                dest["%s[%s]" % (k, dict_k)] = dict_v
        else:
            dest[k] = v


def clean_str_id(id):
    return id.replace("/", "%2F").replace("#", "%23")


def sanitized_url(url):
    parsed = urlparse(url)
    new_path = parsed.path.replace(".", "%2E")
    return parsed._replace(path=new_path).geturl()


def remove_none_from_dict(data):
    return {k: v for k, v in data.items() if v is not None}


async def async_postprocess(self, awaitable, callback, *args, **kwargs):
    obj = await awaitable
    return callback(self, obj, *args, **kwargs)


def awaitable_postprocess(f):
    @functools.wraps(f)
    def wrapped_f(self, obj, *args, **kwargs):
        if asyncio.iscoroutine(obj):
            return async_postprocess(self, obj, f, *args, **kwargs)
        else:
            return f(self, obj, *args, **kwargs)

    return wrapped_f


def inherit_docstrings(cls):
    """Inherit docstrings for methods which doesn't have its' own
    """
    for name, func in getmembers(cls, isfunction):
        if func.__doc__:
            continue

        for parent in cls.__mro__[1:]:
            if hasattr(parent, name):
                func.__doc__ = getattr(parent, name).__doc__
                break
    return cls
