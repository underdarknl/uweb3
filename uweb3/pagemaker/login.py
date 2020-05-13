#!/usr/bin/python
"""uWeb3 PageMaker Mixins for login/authentication purposes.

Contains both the Underdark Login Framework and OpenID implementations
"""

# Standard modules
import binascii
import hashlib
import os
import base64

# Package modules
from uweb3.model import SecureCookie
from .. import model

class User(model.Record):
  """Abstraction for the `user` table."""
  SALT_BYTES = 8

  @classmethod
  def FromName(cls, connection, username):
    """Returns a User object based on the given username."""
    with connection as cursor:
      safe_name = connection.EscapeValues(username)
      user = cursor.Select(
          table=cls.TableName(),
          conditions='name=%s' % safe_name)
    if not user:
      raise cls.NotExistError('No user with name %r' % username)
    return cls(connection, user[0])

  @classmethod
  def HashPassword(cls, password, salt=None):
    if not salt:
      salt = cls.SaltBytes()
    if (len(salt) * 3) / 4 - salt.decode('utf-8').count('=', -2) != cls.SALT_BYTES:
      raise ValueError('Salt is of incorrect length. Expected %d, got: %d' % (
          cls.SALT_BYTES, len(salt)))
    m = hashlib.sha256()
    m.update(password.encode("utf-8") + binascii.hexlify(salt))
    password = m.hexdigest()
    return { 'password': password, 'salt': salt }

  @classmethod
  def SaltBytes(cls):
    """Returns the configured number of random bytes for the salt."""
    random_bytes = os.urandom(cls.SALT_BYTES)
    return base64.b64encode(random_bytes).decode('utf-8').encode('utf-8') #we do this to cast this byte to utf-8

  def UpdatePassword(self, plaintext):
    """Stores a new password hash and salt, from the given plaintext."""
    self.update(self.HashPassword(plaintext))
    self.Save()

  def VerifyChallenge(self, attempt, challenge):
    """Verifies the password hash against the stored hash.

    Both the password hash (attempt) and the challenge should be provided
    as raw bytes.
    """
    password = binascii.hexlify(self['password'])
    actual_pass = hashlib.sha256(password + binascii.hexlify(challenge)).digest()
    return attempt == actual_pass

  def VerifyPlaintext(self, plaintext):
    """Verifies a given plaintext password."""
    salted = self.HashPassword(plaintext, self['salt'].encode('utf-8'))['password']
    return salted == self['password']

