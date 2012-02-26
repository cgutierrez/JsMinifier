import urllib2

class UglifyCall(BaseCall.BaseCall):

    def exec_request():

        data = urllib.urlencode({
            'js_code': self.original,
            'compilation_level': self.level,
            'output_info': "compiled_code" })

        ua = 'Sublime Text - Uglify'
        req = urllib2.Request("http://marijnhaverbeke.nl/uglifyjs", data, headers = { 'User-Agent': ua })
        file = urllib2.urlopen(req, timeout = self.timeout)

        mini_content = file.read().strip()

        if len(mini_content) > 0:
            self.result = re.sub("[\n]+", " ", mini_content) if self.rm_new_lines else mini_content