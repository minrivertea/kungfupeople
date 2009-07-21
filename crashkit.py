# Copyright (c) 2009 Andrey Tarantsov, YourSway LLC (crashkit client)
# Copyright (c) 2006 Bob Ippolito (simplejson)
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__all__ = ['CRASHKIT_VERSION', 'initialize_crashkit', 'send_exception', 'CrashKitDjangoMiddleware', 'CrassKitGAE']

from traceback import extract_tb
from types import ClassType
from datetime import date
import sys
import os
import re

CRASHKIT_VERSION = '1.2.0.25'
CRASHKIT_HOST = 'crashkitapp.appspot.com'
# CRASHKIT_HOST = '8.latest.crashkitapp.appspot.com'
# CRASHKIT_HOST = 'localhost:5005'

BAD_NAME_CHARS_RE = re.compile('[^a-zA-Z0-9]+')

class CrassKitGAE(object):
    
  def handle_exception(self, exception, debug_mode):
    from google.appengine.ext import webapp
    
    request = self.request
    env = {}
    data = {}
    for key, value in request.environ.iteritems():
      if key.startswith('HTTP_') or key.startswith('SERVER_') or key.startswith('REMOTE_') or key in ('PATH_INFO', 'QUERY_STRING'):
        env[key] = value
    for k,v in request.GET.iteritems():  data["G_"  + k] = v
    for k,v in request.POST.iteritems(): data["P_" + k] = v
    for k,v in request.cookies.iteritems(): data["C_" + k] = v
    if hasattr(request, 'session'):
      for k,v in request.session.iteritems(): data["S_" + k] = v
    send_exception(data, env)
    return webapp.RequestHandler.handle_exception(self, exception, debug_mode)
  

class CrashKitDjangoMiddleware(object):
  def __init__(self):
    from django.conf import settings
    initialize_crashkit(**settings.CRASHKIT)
    
  def process_exception(self, request, exception):
    """ Load exceptions into CrashKit """
    try:
      env = {}
      data = {}
      for key, value in request.META.iteritems():
        if key.startswith('HTTP_') or key.startswith('SERVER_') or key.startswith('REMOTE_') or key in ('PATH_INFO', 'QUERY_STRING'):
          env[key] = value
        # else:
        #   print key + " = " + unicode(value)
      for k,v in request.GET.iteritems():  data["G_"  + k] = v
      for k,v in request.POST.iteritems(): data["P_" + k] = v
      for k,v in request.COOKIES.iteritems(): data["C_" + k] = v
      if hasattr(request, 'session'):
        for k,v in request.session.iteritems(): data["S_" + k] = v
      crashkit.send_exception(data, env)
    except Exception:
      raise

def is_parent_dir(parent, child):
  if parent == child:  return True
  if os.path.dirname(child) == child:  return False
  return is_parent_dir(parent, os.path.dirname(child))
  
def determine_role(account_name, product_name):
  if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
    return 'disabled'  # Google App Engine development server

  override_file_name = 'crashkit.%s.role' % BAD_NAME_CHARS_RE.sub('', product_name).lower()
  override_env_name = '%s_CRASHKIT_ROLE' % BAD_NAME_CHARS_RE.sub('_', product_name).upper()
  
  if os.getenv(override_env_name):
    return os.getenv(override_env_name)
    
  try:
    user_home = os.path.expanduser('~')
    
    if os.path.isfile(os.path.join(user_home, override_file_name)):
      return open(os.path.join(user_home, override_file_name)).read().strip()
    
    if os.path.isfile(os.path.join(user_home, '.' + override_file_name)):
      return open(os.path.join(user_home, '.' + override_file_name)).read().strip()
  except ImportError:
    pass  # no such thing as a user home dir (e.g. on Google App Engine)

class CrashKit:
  
  def __init__(self, account_name, product_name, app_dirs=[], app_dir_exclusions=[], role='customer'):
    self.account_name = account_name
    self.product_name = product_name
    self.post_url = "http://%s/%s/products/%s/post-report/0/0" % (
        CRASHKIT_HOST, self.account_name, self.product_name)
    self.app_dirs = [os.path.abspath(d) for d in app_dirs]
    self.app_dir_exclusions = [os.path.abspath(os.path.join(self.app_dirs[0], d)) for d in app_dir_exclusions]
    
    self.role = determine_role(account_name, product_name) or role
    
    for excl_dir in self.app_dir_exclusions:
      if not max([is_parent_dir(app_dir, excl_dir) for app_dir in self.app_dirs]):
        raise ValueError, "Invalid arguments for CrashKit initialization:  Excluded directory '%s' is not (but must be) a parent of any of the application directories: %s." % (excl_dir, ", ".join(["'%s'" % app_dir for app_dir in self.app_dirs]))
        
  def is_app_dir(self, d):
    d = os.path.abspath(d)
    if not self.app_dirs:
      return False
    if not max([is_parent_dir(app_dir, d) for app_dir in self.app_dirs]):
      return False
    if self.app_dir_exclusions and max([is_parent_dir(excl_dir, d) for excl_dir in self.app_dir_exclusions]):
      return False
    return True

  def send_exception(self, data = {}, env = {}):
    if self.role == 'disabled':
      return

    info = sys.exc_info()
    traceback = get_traceback(info[2])
    env = dict(**env)
    env.update(**collect_platform_info())
    message = {
        "exceptions": [
            {
                "name": encode_exception_name(info[0]),
                "message": info[1].message,
                "locations": [encode_location(el, self.is_app_dir) for el in traceback]
            }
        ],
        "data": data,
        "env": env,
        "role": self.role,
        "language": "python",
        "client_version": CRASHKIT_VERSION
    }
    payload = JSONDateEncoder().encode([message])
    from urllib2 import Request, urlopen, HTTPError, URLError
    try:
      response = urlopen(Request(self.post_url, payload))
      the_page = response.read()
      # print unicode(the_page, 'utf-8')
    except UnicodeDecodeError:
      pass
    except HTTPError, e:
      print "Cannot send exception - HTTP error %s" % e.code
      try:
        print unicode(e.read(), 'utf-8')
      except UnicodeDecodeError:
        pass
    except URLError, e:
      print "Cannot send exception: %s" % e.reason
 
crashkit = None

def initialize_crashkit(*args, **kw):
  global crashkit
  crashkit = CrashKit(*args, **kw)
  
def send_exception(data = {}, env = {}):
  crashkit.send_exception(data, env)
 
def get_traceback(tb):
  traceback = []
  while tb != None:
    traceback.append(tb)
    tb = tb.tb_next
  traceback.reverse()
  return traceback

def get_method_name_for_code_object(self, possible_func, code, depth = 0):
  """Given an object and a value of an attribute of that object,
    determines if the value is a bound method or a function implemented by the given code object,
    possibly decorated with one or more decorators.
    
    If it is, returns a best guess on the name of the class the function is bound to.
    Otherwise, returns None."""
  
  if depth > 5: return None
  
  try:
    if code == possible_func.func_code:
      if isinstance(self, ClassType) or isinstance(self, type):
        return self.__name__
      else:
        return self.__class__.__name__
  except AttributeError: pass
  
  try:
    if code == possible_func.im_func.func_code:
      if isinstance(self, ClassType) or isinstance(self, type):
        return self.__name__
      else:
        return possible_func.im_class.__name__
  except AttributeError: pass
  
  try:
    if possible_func.func_closure is not None:
      for cell in possible_func.func_closure:
        try:
          name = get_method_name_for_code_object(self, cell.cell_contents, code, depth + 1)
          if name: return name
        except AttributeError: pass
  except AttributeError: pass

def get_class_name(frame):
  """Guesses a class name to show in a stack trace for the given frame,
  based on the attributes of the first argument of the frame's function."""
  
  code = frame.f_code
  fname = code.co_name
  if code.co_argcount > 0:
    first = code.co_varnames[0]
    self = frame.f_locals[first]
    for key in dir(self):
      try:               attr = getattr(self, key, None)
      except Exception:  attr = None
      if attr is not None:
        name = get_method_name_for_code_object(self, attr, code)
        if name: return name
  return None

def encode_location(traceback, is_app_dir):
  frame = traceback.tb_frame
  co = frame.f_code
  filename, lineno, name = co.co_filename, traceback.tb_lineno, co.co_name
  
  filename = os.path.abspath(filename).replace('\\', '/')
  claimed = is_app_dir(filename)
  
  shortest_package = frame.f_globals.get('__name__')
  if shortest_package is None:  # afaik this only happens while importing a module
    for folder in sys.path:
      folder = os.path.abspath(folder).replace('\\', '/')
      if not folder.endswith('/'):
        folder += '/'
      if filename.startswith(folder):
        package = filename[len(folder):]
        if package.endswith('.py'):  package = package[:-3]
        if package.endswith('.pyc'): package = package[:-4]
        package = package.replace('/', '.')
    
        if shortest_package is None or len(package) < len(shortest_package):
          shortest_package = package
  
  result = { "file": filename, "package": shortest_package, "method": name, "line": lineno, "claimed": claimed }
  class_name = get_class_name(frame)
  if class_name:
    result['class'] = class_name
  return result

def encode_exception_name(exc):
  m = exc.__module__
  c = exc.__name__
  if m == '__main__' or m == 'exceptions':
    return c
  else:
    return '%s.%s' % (m, c)

def collect_platform_info():
  import platform
  env = {}
  env['os_kernel_name'] = platform.system()
  env['os_kernel_version'] = platform.release()
  if 'Linux' == platform.system():
    env['os_dist'] = ' '.join(platform.dist()).strip()
  env['cpu_arch'] = platform.architecture()[0]
  env['cpu_type'] = platform.processor()
  env['python_version'] = platform.python_version()
  return env
  
import re

c_encode_basestring_ascii = None
c_make_encoder = None

ESCAPE = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]')
ESCAPE_ASCII = re.compile(r'([\\"]|[^\ -~])')
HAS_UTF8 = re.compile(r'[\x80-\xff]')
ESCAPE_DCT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}
for i in range(0x20):
    #ESCAPE_DCT.setdefault(chr(i), '\\u{0:04x}'.format(i))
    ESCAPE_DCT.setdefault(chr(i), '\\u%04x' % (i,))

# Assume this produces an infinity on all machines (probably not guaranteed)
INFINITY = float('1e66666')
FLOAT_REPR = repr

def encode_basestring(s):
    """Return a JSON representation of a Python string

    """
    def replace(match):
        return ESCAPE_DCT[match.group(0)]
    return '"' + ESCAPE.sub(replace, s) + '"'


def py_encode_basestring_ascii(s):
    """Return an ASCII-only JSON representation of a Python string

    """
    if isinstance(s, str) and HAS_UTF8.search(s) is not None:
        s = s.decode('utf-8')
    def replace(match):
        s = match.group(0)
        try:
            return ESCAPE_DCT[s]
        except KeyError:
            n = ord(s)
            if n < 0x10000:
                #return '\\u{0:04x}'.format(n)
                return '\\u%04x' % (n,)
            else:
                # surrogate pair
                n -= 0x10000
                s1 = 0xd800 | ((n >> 10) & 0x3ff)
                s2 = 0xdc00 | (n & 0x3ff)
                #return '\\u{0:04x}\\u{1:04x}'.format(s1, s2)
                return '\\u%04x\\u%04x' % (s1, s2)
    return '"' + str(ESCAPE_ASCII.sub(replace, s)) + '"'


encode_basestring_ascii = c_encode_basestring_ascii or py_encode_basestring_ascii

class JSONEncoder(object):
    """Extensible JSON <http://json.org> encoder for Python data structures.

    Supports the following objects and types by default:

    +-------------------+---------------+
    | Python            | JSON          |
    +===================+===============+
    | dict              | object        |
    +-------------------+---------------+
    | list, tuple       | array         |
    +-------------------+---------------+
    | str, unicode      | string        |
    +-------------------+---------------+
    | int, long, float  | number        |
    +-------------------+---------------+
    | True              | true          |
    +-------------------+---------------+
    | False             | false         |
    +-------------------+---------------+
    | None              | null          |
    +-------------------+---------------+

    To extend this to recognize other objects, subclass and implement a
    ``.default()`` method with another method that returns a serializable
    object for ``o`` if possible, otherwise it should call the superclass
    implementation (to raise ``TypeError``).

    """
    item_separator = ', '
    key_separator = ': '
    def __init__(self, skipkeys=False, ensure_ascii=True,
            check_circular=True, allow_nan=True, sort_keys=False,
            indent=None, separators=None, encoding='utf-8', default=None):
        """Constructor for JSONEncoder, with sensible defaults.

        If skipkeys is false, then it is a TypeError to attempt
        encoding of keys that are not str, int, long, float or None.  If
        skipkeys is True, such items are simply skipped.

        If ensure_ascii is true, the output is guaranteed to be str
        objects with all incoming unicode characters escaped.  If
        ensure_ascii is false, the output will be unicode object.

        If check_circular is true, then lists, dicts, and custom encoded
        objects will be checked for circular references during encoding to
        prevent an infinite recursion (which would cause an OverflowError).
        Otherwise, no such check takes place.

        If allow_nan is true, then NaN, Infinity, and -Infinity will be
        encoded as such.  This behavior is not JSON specification compliant,
        but is consistent with most JavaScript based encoders and decoders.
        Otherwise, it will be a ValueError to encode such floats.

        If sort_keys is true, then the output of dictionaries will be
        sorted by key; this is useful for regression tests to ensure
        that JSON serializations can be compared on a day-to-day basis.

        If indent is a non-negative integer, then JSON array
        elements and object members will be pretty-printed with that
        indent level.  An indent level of 0 will only insert newlines.
        None is the most compact representation.

        If specified, separators should be a (item_separator, key_separator)
        tuple.  The default is (', ', ': ').  To get the most compact JSON
        representation you should specify (',', ':') to eliminate whitespace.

        If specified, default is a function that gets called for objects
        that can't otherwise be serialized.  It should return a JSON encodable
        version of the object or raise a ``TypeError``.

        If encoding is not None, then all input strings will be
        transformed into unicode using that encoding prior to JSON-encoding.
        The default is UTF-8.

        """

        self.skipkeys = skipkeys
        self.ensure_ascii = ensure_ascii
        self.check_circular = check_circular
        self.allow_nan = allow_nan
        self.sort_keys = sort_keys
        self.indent = indent
        if separators is not None:
            self.item_separator, self.key_separator = separators
        if default is not None:
            self.default = default
        self.encoding = encoding

    def default(self, o):
        """Implement this method in a subclass such that it returns
        a serializable object for ``o``, or calls the base implementation
        (to raise a ``TypeError``).

        For example, to support arbitrary iterators, you could
        implement default like this::

            def default(self, o):
                try:
                    iterable = iter(o)
                except TypeError:
                    pass
                else:
                    return list(iterable)
                return JSONEncoder.default(self, o)

        """
        raise TypeError(repr(o) + " is not JSON serializable")

    def encode(self, o):
        """Return a JSON string representation of a Python data structure.

        >>> JSONEncoder().encode({"foo": ["bar", "baz"]})
        '{"foo": ["bar", "baz"]}'

        """
        # This is for extremely simple cases and benchmarks.
        if isinstance(o, basestring):
            if isinstance(o, str):
                _encoding = self.encoding
                if (_encoding is not None
                        and not (_encoding == 'utf-8')):
                    o = o.decode(_encoding)
            if self.ensure_ascii:
                return encode_basestring_ascii(o)
            else:
                return encode_basestring(o)
        # This doesn't pass the iterator directly to ''.join() because the
        # exceptions aren't as detailed.  The list call should be roughly
        # equivalent to the PySequence_Fast that ''.join() would do.
        chunks = self.iterencode(o, _one_shot=True)
        if not isinstance(chunks, (list, tuple)):
            chunks = list(chunks)
        return ''.join(chunks)

    def iterencode(self, o, _one_shot=False):
        """Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring
        if self.encoding != 'utf-8':
            def _encoder(o, _orig_encoder=_encoder, _encoding=self.encoding):
                if isinstance(o, str):
                    o = o.decode(_encoding)
                return _orig_encoder(o)

        def floatstr(o, allow_nan=self.allow_nan, _repr=FLOAT_REPR, _inf=INFINITY, _neginf=-INFINITY):
            # Check for specials.  Note that this type of test is processor- and/or
            # platform-specific, so do tests which don't depend on the internals.

            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text


        if _one_shot and c_make_encoder is not None and not self.indent and not self.sort_keys:
            _iterencode = c_make_encoder(
                markers, self.default, _encoder, self.indent,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, self.allow_nan)
        else:
            _iterencode = _make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot)
        return _iterencode(o, 0)

def _make_iterencode(markers, _default, _encoder, _indent, _floatstr, _key_separator, _item_separator, _sort_keys, _skipkeys, _one_shot,
        ## HACK: hand-optimized bytecode; turn globals into locals
        False=False,
        True=True,
        ValueError=ValueError,
        basestring=basestring,
        dict=dict,
        float=float,
        id=id,
        int=int,
        isinstance=isinstance,
        list=list,
        long=long,
        str=str,
        tuple=tuple,
    ):

    def _iterencode_list(lst, _current_indent_level):
        if not lst:
            yield '[]'
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = '['
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + (' ' * (_indent * _current_indent_level))
            separator = _item_separator + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = _item_separator
        first = True
        for value in lst:
            if first:
                first = False
            else:
                buf = separator
            if isinstance(value, basestring):
                yield buf + _encoder(value)
            elif value is None:
                yield buf + 'null'
            elif value is True:
                yield buf + 'true'
            elif value is False:
                yield buf + 'false'
            elif isinstance(value, (int, long)):
                yield buf + str(value)
            elif isinstance(value, float):
                yield buf + _floatstr(value)
            else:
                yield buf
                if isinstance(value, (list, tuple)):
                    chunks = _iterencode_list(value, _current_indent_level)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, _current_indent_level)
                else:
                    chunks = _iterencode(value, _current_indent_level)
                for chunk in chunks:
                    yield chunk
        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + (' ' * (_indent * _current_indent_level))
        yield ']'
        if markers is not None:
            del markers[markerid]

    def _iterencode_dict(dct, _current_indent_level):
        if not dct:
            yield '{}'
            return
        if markers is not None:
            markerid = id(dct)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield '{'
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + (' ' * (_indent * _current_indent_level))
            item_separator = _item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator
        first = True
        if _sort_keys:
            items = dct.items()
            items.sort(key=lambda kv: kv[0])
        else:
            items = dct.iteritems()
        for key, value in items:
            if isinstance(key, basestring):
                pass
            # JavaScript is weakly typed for these, so it makes sense to
            # also allow them.  Many encoders seem to do something like this.
            elif isinstance(key, float):
                key = _floatstr(key)
            elif key is True:
                key = 'true'
            elif key is False:
                key = 'false'
            elif key is None:
                key = 'null'
            elif isinstance(key, (int, long)):
                key = str(key)
            elif _skipkeys:
                continue
            else:
                raise TypeError("key " + repr(key) + " is not a string")
            if first:
                first = False
            else:
                yield item_separator
            yield _encoder(key)
            yield _key_separator
            if isinstance(value, basestring):
                yield _encoder(value)
            elif value is None:
                yield 'null'
            elif value is True:
                yield 'true'
            elif value is False:
                yield 'false'
            elif isinstance(value, (int, long)):
                yield str(value)
            elif isinstance(value, float):
                yield _floatstr(value)
            else:
                if isinstance(value, (list, tuple)):
                    chunks = _iterencode_list(value, _current_indent_level)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, _current_indent_level)
                else:
                    chunks = _iterencode(value, _current_indent_level)
                for chunk in chunks:
                    yield chunk
        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + (' ' * (_indent * _current_indent_level))
        yield '}'
        if markers is not None:
            del markers[markerid]

    def _iterencode(o, _current_indent_level):
        if isinstance(o, basestring):
            yield _encoder(o)
        elif o is None:
            yield 'null'
        elif o is True:
            yield 'true'
        elif o is False:
            yield 'false'
        elif isinstance(o, (int, long)):
            yield str(o)
        elif isinstance(o, float):
            yield _floatstr(o)
        elif isinstance(o, (list, tuple)):
            for chunk in _iterencode_list(o, _current_indent_level):
                yield chunk
        elif isinstance(o, dict):
            for chunk in _iterencode_dict(o, _current_indent_level):
                yield chunk
        else:
            if markers is not None:
                markerid = id(o)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = o
            o = _default(o)
            for chunk in _iterencode(o, _current_indent_level):
                yield chunk
            if markers is not None:
                del markers[markerid]

    return _iterencode

#idea by https://mdp.cti.depaul.edu/web2py_wiki/default/wiki/JSONdatetime
import datetime
class JSONDateEncoder(JSONEncoder):
   def default(self, obj):
       if isinstance(obj, datetime.datetime):
           return '**new Date(%i,%i,%i,%i,%i,%i)' % (obj.year,
                                                     obj.month-1,
                                                     obj.day,
                                                     obj.hour,
                                                     obj.minute,
                                                     obj.second)
       if isinstance(obj, datetime.date):
           return '**new Date(%i,%i,%i)' % (obj.year,
                                            obj.month-1,
                                            obj.day)
       return JSONEncoder.default(self, obj)
