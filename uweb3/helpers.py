import os
import time
import mimetypes
import datetime
from wsgiref.headers import Headers
from uweb3.pagemaker import MimeTypeDict


RFC_1123_DATE = '%a, %d %b %Y %T GMT'

# Search File
def is_accessible(abs_file_path):
    return (
        os.path.exists(abs_file_path) and
        os.path.isfile(abs_file_path) and
        os.access(abs_file_path, os.R_OK)
    )


def search_file(relative_file_path, dirs):
  for d in dirs:
    if not os.path.isabs(d):
      d = os.path.abspath(d) + os.sep

    file = os.path.join(d, relative_file_path)
    if is_accessible(file):
      return file


# Header utils
def get_content_length(filename):
  stats = os.stat(filename)
  return str(stats.st_size)


def generate_last_modified(filename):
  stats = os.stat(filename)
  last_modified = time.strftime("%a, %d %b %Y %H:%M:%sS GMT", time.gmtime(stats.st_mtime))
  return last_modified


def get_content_type(mimetype, charset):
  if mimetype.startswith('text/') or mimetype == 'application/javascript':
      mimetype += '; charset={}'.format(charset)
  return mimetype


# Response body iterator
def _iter_and_close(file_obj, block_size, charset):
    """Yield file contents by block then close the file."""
    while True:
        try:
            block = file_obj.read(block_size)
            if block:
                if isinstance(block, bytes):
                    yield block
                else:
                    yield block.encode(charset)
            else:
                raise StopIteration
        except StopIteration:
            file_obj.close()
            break


def _get_body(filename, method, block_size, charset):
    if method == 'HEAD':
        return [b'']
    return _iter_and_close(open(filename, 'rb'), block_size, charset)


# View functions
def static_file_view(env, start_response, filename, block_size, charset, CACHE_DURATION):
    method = env['REQUEST_METHOD'].upper()
    if method not in ('HEAD', 'GET'):
        start_response('405 METHOD NOT ALLOWED',
                       [('Content-Type', 'text/plain; UTF-8')])
        return [b'']
    mimetype, encoding = mimetypes.guess_type(filename)
    headers = Headers([])

    cache_days = CACHE_DURATION.get(mimetype, 0)
    expires = datetime.datetime.utcnow() + datetime.timedelta(cache_days)
    headers.add_header('Cache-control', f'public, max-age={expires.strftime(RFC_1123_DATE)}')
    headers.add_header('Expires', expires.strftime(RFC_1123_DATE))
    if env.get('HTTP_IF_MODIFIED_SINCE'):
      if env.get('HTTP_IF_MODIFIED_SINCE') >= generate_last_modified(filename):
        start_response('304 ok', headers.items())
        return [b'304']
    headers.add_header('Content-Encodings', encoding)
    if mimetype:
        headers.add_header('Content-Type', get_content_type(mimetype, charset))
    headers.add_header('Content-Length', get_content_length(filename))
    headers.add_header('Last-Modified', generate_last_modified(filename))
    headers.add_header("Accept-Ranges", "bytes")
    start_response('200 OK', headers.items())
    return _get_body(filename, method, block_size, charset)


def http404(env, start_response):
  start_response('404 Not Found',
                  [('Content-type', 'text/plain; charset=utf-8')])
  return [b'404 Not Found']

#This code is copied and altered from the WSGI static middleware PyPi package
#https://pypi.org/project/wsgi-static-middleware/
class StaticMiddleware:
    CACHE_DURATION = MimeTypeDict({'text': 7, 'image': 30, 'application': 7})

    def __init__(self, app, static_root, static_dirs=None,
                block_size=16*4096, charset='UTF-8'):
      self.app = app
      self.static_root = static_root.lstrip('/').rstrip('/')
      if static_dirs is None:
          static_dirs = [os.path.join(os.path.abspath('.'), 'static')]
      self.static_dirs = static_dirs
      self.charset = charset
      self.block_size = block_size

    def __call__(self, env, start_response):
      path = env['PATH_INFO'].lstrip('/')
      if path.startswith(self.static_root):
        relative_file_path = '/'.join(path.split('/')[1:])
        p = os.path.join(self.static_dirs[0], relative_file_path)
        if os.path.commonprefix((os.path.realpath(p), self.static_dirs[0])) != self.static_dirs[0]:
          return http404(env, start_response)
        return self.handle(env, start_response, relative_file_path)
      return self.app(env, start_response)

    def handle(self, env, start_response, filename):
      abs_file_path = search_file(filename, self.static_dirs)
      if abs_file_path:
        res = static_file_view(env, start_response, abs_file_path,
                                self.block_size, self.charset, self.CACHE_DURATION)
        return res
      else:
        return http404(env, start_response)
