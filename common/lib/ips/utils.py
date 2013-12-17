# Copoyright (c) 2013, Masato Taruishi <taru0216@gmail.com>


__author__ = 'Masato Taruishi'
__copyright__ = 'Copyright (c) 2013, Masato Taruishi <taru0216@gmail.com>'


import logging
import os.path
import socket
import subprocess
import sys
import tornado.options


class Error(Exception):
  """Base error class of this module."""
  pass


class CommandExitedWithError(Error):
  """Thrown when the specified command exited error.

  >>> CallExternalCommand('false')
  Traceback (most recent call last):
    ...
  CommandExitedWithError: command "false" exited with an error: 1: 
  """
  def __init__(self, cmd, retval, out):
    self.cmd = cmd
    self.retval = retval
    self.out = out

  def __str__(self):
    return 'command "%s" exited with an error: %d: %s' % (self.cmd,
                                                          self.retval,
                                                          self.out)


def CallExternalCommand(cmd):
  """Calls the specified external command.

  >>> CallExternalCommand('echo hello')
  u'hello\\n'

  """
  buf = ''
  for line in ExternalCommand(cmd):
    buf += line
  return buf


class ExternalCommand():
  """Eexternal command.

  >>> cmd = ExternalCommand('echo hello && echo world')
  >>> for line in cmd:
  ...   print line.strip()
  hello
  world

  """

  def __iter__(self):
    return self

  def __init__(self, cmd):
    """Instantiates an external command object for the specified cmd."""
    logging.debug('executing %s', cmd)
    self.cmd = cmd
    self.p = subprocess.Popen(cmd, shell=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    self.out = ''
    self.retval = None

  def Kill(self):
    """Kills the external command.

    >>> cmd = ExternalCommand('while true; do echo hello; sleep 1; done')
    >>> for line in cmd:
    ...   cmd.Kill()
    Traceback (most recent call last):
      ...
    CommandExitedWithError: command "while true; do echo hello; sleep 1; done" exited with an error: -9: hello
    <BLANKLINE>

    """
    logging.debug('sending term signal to %s', self.p)
    self.p.kill()
    self.retval = self.p.wait()
    logging.debug('cmd "%s" exited: %d', self.cmd, self.retval)

  def next(self):
    """Returns the next line generated by the external command."""
    if not self.p:
      raise StopIteration

    line = self.p.stdout.readline()
    if line == '':
      self.retval = self.p.wait()
      logging.debug('cmd "%s" exited: %d', self.cmd, self.retval)
      self.p = None
      if self.retval:
        raise CommandExitedWithError(self.cmd, self.retval, self.out)
      raise StopIteration

    line = unicode(line, 'utf-8')
    logging.debug('got a line from "%s": %s', self.cmd, line)
    self.out += line
    return line


def GetDataDir():
  """Returns the directory for data files.

  >>> GetDataDir()
  '/usr/share/ips-common'

  """
  return os.path.sep.join([sys.prefix, 'share', 'ips-common'])


def GetDataFile(file):
  """Open data file path in for ips.

  This returns a file path for data file. If there's
  the file which has the same name in the current directory,
  then the file is returned instead.
  """

  path = GetDataDir() + os.path.sep + file
  if os.path.exists(file):
    path = file
  return path


def GetNetworkAddresses(dev=None):
  """Gets IP addresses.

  If dev is specified, then the addresses on the device are returned.

  >>> GetNetworkAddress()

  >>> GetNetworkAddress('eth1')

  """
  if not dev:
    dev=CallExternalCommand('ip route | grep default | cut -d" " -f5').strip()
    if not dev:
      dev='eth0'
  return CallExternalCommand(
      'ip addr show dev %s | grep "scope global" | '
      "awk -F' ' '{print $2;}' | cut -d/ -f1" % dev).strip().split()


def GetHostPortForUrl(host, port):
  if host.find(':') != -1:
    host = '[' + host + ']'
  return '%s:%s' % (host, port)


if __name__ == '__main__':
  import doctest
  doctest.testmod()