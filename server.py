#!/usr/bin/env python3
 
"""Simple HTTP Server With Upload.
This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.
see: https://gist.github.com/UniIsland/3346170
"""
 
 
__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]
__author__ = "bones7456"
__home_page__ = "http://li2z.cn/"
 
import os
import posixpath
import http.server
import http.cookies
import html
import urllib.request, urllib.parse, urllib.error
import cgi
import shutil
import mimetypes
import re
from io import BytesIO
 
 
class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
 
    """Simple HTTP request handler with GET/HEAD/POST commands.
    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.
    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.
    """
 
    server_version = "SimpleHTTPWithUpload/" + __version__
 
    def do_GET(self, cookie=None):
        """Serve a GET request."""
        if len(self.path) < 2 and self.is_auth_normal_user1():
            self.path = "/normal_user1"
        if len(self.path) < 2 and self.is_auth_normal_user2():
            self.path = "/normal_user2"
        if len(self.path) < 2 and self.is_auth_admin():
            self.path = "/admin"
        if not "specialChar" in self.path and not ".png" in self.path and not self.is_auth() and not self.path.startswith("/chatroom"):
            self.path = "/"
        f = self.send_head(cookie)
        if f:
            self.copyfile(f, self.wfile)
            f.close()
 
    def is_auth_normal_user1(self):
        cookies = self.get_cookies()
        return cookies.get("normal_user1") == "ok"

    def is_auth_normal_user2(self):
        cookies = self.get_cookies()
        return cookies.get("normal_user2") == "ok"

    def is_auth_admin(self):
        cookies = self.get_cookies()
        return cookies.get("admin") == "ok"

    def is_auth(self):
        cookies = self.get_cookies()
        return (cookies.get("normal_user1") == "ok") or (cookies.get("normal_user2") == "ok") or (cookies.get("admin") == "ok")

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()
 
    def extract_POST_data(self):
        retdict = {}
        data = self.rfile.read(int(self.headers['Content-Length']))
        for keyvalue in data.decode().split('&'):
            key, value = keyvalue.split('=')
            retdict[key] = value
        return retdict

    def get_cookies(self):
        retdict = {}
        data = self.headers.get('Cookie')
        if data is not None:
            for keyvalue in data.split(';'):
                key, value = keyvalue.split('=')
                retdict[key.strip()] = value.strip()
        return retdict
    
    def do_POST(self):
        """Serve a POST request."""
        if not self.pathstartswith('/chatroom'):
          if self.headers["Content-Type"] == "application/x-www-form-urlencoded":
              data = self.extract_POST_data()
              cookie = None
              if data.get('psw') == "password":
                  cookie = http.cookies.SimpleCookie()
                  cookie['normal_user1'] = "ok"
                  self.headers['Cookie'] = "normal_user1=ok" 

              if data.get('psw').replace(' ', "") == "'OR1=1--":
                  cookie = http.cookies.SimpleCookie()
                  cookie['normal_user2'] = "ok"
                  self.headers['Cookie'] = "normal_user2=ok" 

              if data.get('psw') == "hardToGuessPassword":
                  cookie = http.cookies.SimpleCookie()
                  cookie['admin'] = "ok"
                  self.headers['Cookie'] = "admin=ok" 

              self.do_GET(cookie)
              return
          r, info = self.deal_post_data()
          print((r, info, "by: ", self.client_address))
          f = BytesIO()
          f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
          f.write(b"<html>\n<title>Upload Result Page</title>\n")
          f.write(b"<body>\n<h2>Upload Result Page</h2>\n")
          f.write(b"<hr>\n")
          if r:
              f.write(b"<strong>Success:</strong>")
          else:
              f.write(b"<strong>Failed:</strong>")
          f.write(info.encode())
          f.write(("<br><a href=\"%s\">back</a>" % self.headers['referer']).encode())
          f.write(b"<hr><small>Powerd By: bones7456, check new version at ")
          f.write(b"<a href=\"http://li2z.cn/?s=SimpleHTTPServerWithUpload\">")
          f.write(b"here</a>.</small></body>\n</html>\n")
          length = f.tell()
          f.seek(0)
          self.send_response(200)
          self.send_header("Content-type", "text/html")
          self.send_header("Content-Length", str(length))
          self.end_headers()
          if f:
              self.copyfile(f, self.wfile)
              f.close()
        else:
          # push the posts messages to the chat server HERE
          pass
        
    def login(self):
        pass

    def deal_post_data(self):
        content_type = self.headers['content-type']
        if not content_type:
            return (False, "Content-Type header doesn't contain boundary")
        boundary = content_type.split("=")[1].encode()
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
        if not fn:
            return (False, "Can't find out file name...")
        path = self.translate_path(self.path)
        fn = os.path.join(path, fn[0])
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith(b'\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, "File '%s' upload success!" % fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")
 
    def send_head(self, cookie=None):
        """Common code for GET and HEAD commands.
        This sends the response code and MIME headers.
        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if any([elt in self.path for elt in ['Nicky', 'Andr', 'Florence', 'evg_olivier_fZQeD', 'Villefort']]):
                return self.list_images(path)
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                if cookie:
                    print("SENDING COOKIES IN HEADER")
                    self.send_header("Set-Cookie", cookie.output(header='', sep=''))
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.send_response(404)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        if cookie:
            print("SENDING COOKIES IN HEADER")
            self.send_header("Set-Cookie", cookie.output(header='', sep=''))
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_images(self, path):
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        dirname = os.path.basename(path)
        replacement = ""
        f = BytesIO()
        result = open('normal_user1/image.template', 'r').read()
        displaypath = cgi.escape(urllib.parse.unquote(self.path))
        for name in list:
            fullname = os.path.join(path, name)
            if '.JPG' in fullname.upper():
                replacement += '<img height="612" data-src="{}" src="blank.gif" class="lazy" alt="{}" title="{}">\n'.format('/normal_user1/'+ dirname + '/' + name, name, name)
        result = result.replace('$@REPLACEME@$', replacement)
        f.write(result.encode())
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

 
    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.
        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)
        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = [_f for _f in words if _f]
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path
 
    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.
        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).
        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.
        """
        shutil.copyfileobj(source, outputfile)
 
    def guess_type(self, path):
        """Guess the type of a file.
        Argument is a PATH (a filename).
        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.
        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.
        """
 
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']
 
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })
 
 
def main(handler_class = SimpleHTTPRequestHandler,
         server_class = http.server.ThreadingHTTPServer):
    server_address = ('', 8080)
    server_chatroom = ('', 8081)
    httpd = server_class(server_address, handler_class)
    #httpdChatroom = server_class(server_chatroom, handler_class)
    httpd.serve_forever()
    #httpdChatroom.serve_forever()
 
if __name__ == '__main__':
    main()

