import sublime, sublime_plugin
import urllib
import urllib2
import threading

class GoogleClosureCall(threading.Thread):

    def __init__(self, sel, string, timeout):
        self.sel = sel
        self.original = string
        self.timeout = timeout
        self.result = None
        threading.Thread.__init__(self)

    def run(self):

        try:
            data = urllib.urlencode({
                'js_code': self.original,
                'compilation_level': "WHITESPACE_ONLY",
                'output_info': "compiled_code" })

            ua = 'Sublime Text - Google Closure'
            req = urllib2.Request("http://closure-compiler.appspot.com/compile", data, headers = { 'User-Agent': ua })
            file = urllib2.urlopen(req, timeout = self.timeout)
            self.result = file.read()
            return
        except (urllib2.HTTPError) as (e):
            err = '%s: HTTP error %s contacting API' % (__name__, str(e.code))
        except (urllib2.URLError) as (e):
            err = '%s: URL error %s contacting API' % (__name__, str(e.code))

        sublime.error_message(err)
        self.result = False