#!/usr/bin/python
"""uWeb3 PageMaker Mixins for login/authentication purposes.

Contains both the Underdark Login Framework and OpenID implementations
"""

# Standard modules
import binascii
import hashlib
import os
import base64

# Third-party modules
import simplejson

# Package modules
from uweb3.model import SecureCookie
from . import login_openid
from .. import model
from .. import response

OPENID_PROVIDERS = {'google': 'https://www.google.com/accounts/o8/id',
                    'yahoo': 'http://yahoo.com/',
                    'myopenid': 'http://myopenid.com/'}


# ##############################################################################
# Record classes for Underdark Login Framework
#
class Challenge(model.Record):
  """Abstraction for the `challenge` table."""
  _PRIMARY_KEY = 'user', 'remote'
  CHALLENGE_BYTES = 16

  @classmethod
  def ChallengeBytes(cls):
    """Returns the configured number of random bytes for a challenge."""
    return os.urandom(cls.CHALLENGE_BYTES)

  @classmethod
  def MakeChallenge(cls, connection, remote, user):
    """Makes a new, or retrieves an existing challenge for a given IP + user."""
    record = {'remote': remote, 'user': user, 'challenge': cls.ChallengeBytes()}
    try:
      return super(Challenge, cls).Create(connection, record)
    except connection.IntegrityError:
      return cls.FromPrimary(connection, (user, remote))


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


# ##############################################################################
# Actual Pagemaker mixin class
#
class LoginMixin(SecureCookie):
  """Provides the Login Framework for uWeb3."""
  ULF_CHALLENGE = Challenge
  ULF_USER = User

  def ValidateLogin(self):
    user = self.ULF_USER.FromName(
        self.connection, self.post.getfirst('username'))
    if user.VerifyPlaintext(str(self.post.getfirst('password', ''))):
      return self._Login_Success(user)
    return self._Login_Failure()

  def _Login_Success(self, user):
    """Renders the response to the user upon authentication failure."""
    raise NotImplementedError

  def _ULF_Success(self, secure):
    """Renders the response to the user upon authentication success."""
    raise NotImplementedError


class OpenIdMixin(object):
  """A class that provides rudimentary OpenID authentication.

  At present, it does not support any means of Attribute Exchange (AX) or other
  account information requests (sReg). However, it does provide the base
  necessities for verifying that whoever logs in is still the same person as the
  one that was previously registered.
  """
  def _OpenIdInitiate(self, provider=None):
    """Verifies the supplied OpenID URL and resolves a login through it."""
    if provider:
      try:
        openid_url = OPENID_PROVIDERS[provider.lower()]
      except KeyError:
        return self.OpenIdProviderError('Invalid OpenID provider %r' % provider)
    else:
      openid_url = self.post.getfirst('openid_provider')

    consumer = login_openid.OpenId(self.req)
    # set the realm that we want to ask to user to verify to
    trustroot = 'http://%s' % self.req.env['HTTP_HOST']
    # set the return url that handles the validation
    returnurl = trustroot + '/OpenIDValidate'

    try:
      return consumer.Verify(openid_url, trustroot, returnurl)
    except login_openid.InvalidOpenIdUrl as error:
      return self.OpenIdProviderBadLink(error)
    except login_openid.InvalidOpenIdService as error:
      return self.OpenIdProviderError(error)

  def _OpenIdValidate(self):
    """Handles the return url that openId uses to send the user to"""
    try:
      auth_dict = login_openid.OpenId(self.req).doProcess()
    except login_openid.VerificationFailed as error:
      return self.OpenIdAuthFailure(error)
    except login_openid.VerificationCanceled as error:
      return self.OpenIdAuthCancel(error)
    return self.OpenIdAuthSuccess(auth_dict)

  def OpenIdProviderBadLink(self, err_obj):
    """Handles the case where the OpenID provider link is faulty."""
    raise NotImplementedError

  def OpenIdProviderError(self, err_obj):
    """Handles the case where the OpenID provider responds out of spec."""
    raise NotImplementedError

  def OpenIdAuthCancel(self, err_obj):
    """Handles the case where the client cancels OpenID authentication."""
    raise NotImplementedError

  def OpenIdAuthFailure(self, err_obj):
    """Handles the case where the provided authentication is invalid."""
    raise NotImplementedError

  def OpenIdAuthSuccess(self, auth_dict):
    """Handles the case where the OpenID authentication was successful.

    Implementers should at the very least override this method as this is where
    you will want to mark people as authenticated, either by cookies or sessions
    tracked otherwise.
    """
    raise NotImplementedError
