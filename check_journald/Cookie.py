#!/bin/python

"""
	The following Class is a modified version of the Cookie Class found in the python nagiosplugin module.
	Download: https://pypi.org/project/nagiosplugin/#files
"""

import os
import fcntl
import tempfile
import codecs
import json

try:
    from collections import UserDict
except ImportError:
    from UserDict import UserDict

class Cookie(UserDict, object):

	def __init__(self, statefile=None):
		super(self)
		self.path = statefile
		self.file_obj = None
		
	def __enter__(self):
        """Allows Cookie to be used as context manager.

        Opens the file and passes a dict-like object into the
        subordinate context. See :meth:`open` for details about opening
        semantics. When the context is left in the regular way (no
        exception raised), the cookie is :meth:`commit`\ ted to disk.

        :yields: open cookie
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self.commit()
        self.close()

	def open(self):
        """Reads/creates the state file and initializes the dict.

        If the state file does not exist, it is touched into existence.
        An exclusive lock is acquired to ensure serialized access. If
        :meth:`open` fails to parse file contents, it truncates
        the file before raising an exception. This guarantees that
        plugins will not fail repeatedly when their state files get
        damaged.

        :returns: Cookie object (self)
        :raises ValueError: if the state file is corrupted or does not
            deserialize into a dict
        """
        self.file_obj = self._create_file_object()
        self._file_lock_exclusive(self.file_obj)
        if os.fstat(self.file_obj.fileno()).st_size:
            try:
                self.data = self._load()
            except ValueError:
                self.file_obj.truncate(0)
                raise
        return self
		
	def _create_file_object(self):
        if not self.path:
			return tempfile.TemporaryFile(mode='w+', encoding='acsii', 
								suffix='', prefix='plugin_cookie_', dir=None)
        # mode='a+' has problems with mixed R/W operation on Mac OS X
        try:
            return codecs.open(self.path, 'r+', encoding='ascii')
        except IOError:
            return codecs.open(self.path, 'w+', encoding='ascii')

    def _load(self):
        self.file_obj.seek(0)
        data = json.load(self.file_obj)
        if not isinstance(data, dict):
            raise ValueError('format error: cookie does not contain dict',
                             self.path, data)
        return data

    def close(self):
        """Closes a cookie and its underlying state file.

        This method has no effect if the cookie is already closed.
        Once the cookie is closed, any operation (like :meth:`commit`)
        will raise an exception.
        """
        if not self.file_obj:
            return
        self.file_obj.close()
        self.file_obj = None

    def commit(self):
        """Persists the cookie's dict items in the state file.

        The cookies content is serialized as JSON string and saved to
        the state file. The buffers are flushed to ensure that the new
        content is saved in a durable way.
        """
        if not self.file_obj:
            raise IOError('cannot commit closed cookie', self.path)
        self.file_obj.seek(0)
        self.file_obj.truncate()
        json.dump(self.data, self.file_obj)
        self.file_obj.write('\n')
        self.file_obj.flush()
        os.fsync(self.file_obj)
	
	def _file_lock_exclusive(self, file):
		"""Acquire Exclusive File Lock (POSIX Only)"""
		fcntl.flock(file, fcntl.LOCK_EX)