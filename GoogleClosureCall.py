import sublime
import sublime_plugin
import urllib
import urllib2
import threading
import re

class GoogleClosureCall(threading.Thread):

    def __init__(self, sel, string, timeout, level, rm_new_lines):
        self.sel = sel
        self.original = string
        self.timeout = timeout
        self.result = None
        self.level = level
        self.rm_new_lines = rm_new_lines
        threading.Thread.__init__(self)

    def run(self):

        try:
            data = urllib.urlencode({
                'js_code': self.original,
                'compilation_level': self.level,
                'output_info': "compiled_code" })

            ua = 'Sublime Text - Google Closure'
            req = urllib2.Request("http://closure-compiler.appspot.com/compile", data, headers = { 'User-Agent': ua })
            file = urllib2.urlopen(req, timeout = self.timeout)

            mini_content = file.read().strip()

            if len(mini_content) > 0:
                self.result = re.sub("[\n]+", " ", mini_content) if self.rm_new_lines else mini_content

            return
        except (urllib2.HTTPError) as (e):
            err = '%s: HTTP error %s contacting API' % (__name__, str(e.code))
        except (urllib2.URLError) as (e):
            err = '%s: URL error %s contacting API' % (__name__, str(e.code))

        sublime.error_message(err)