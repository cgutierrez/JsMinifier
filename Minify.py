import sublime
import sublime_plugin

from compilers import GoogleClosureCall, UglifyCall

class Minify(sublime_plugin.TextCommand):

    def run(self, edit):

        selections = self.view.sel()
        settings = sublime.load_settings("Minifier.sublime-settings")

        # check if the user has any actual selections
        has_selections = False
        for sel in selections:
            if sel.empty() == False:
                has_selections = True

        # if not, add the entire file as a selection
        if not has_selections:
            full_region = sublime.Region(0, self.view.size())
            selections.add(full_region)

        threads = []
        for sel in selections:
            selbody = self.view.substr(sel)

            CompilerCall = self.get_minifier(settings)

            thread = CompilerCall(
                        sel,
                        selbody,
                        timeout=5,
                        level=settings.get('optimization_level', "WHITESPACE_ONLY"),
                        rm_new_lines=settings.get('remove_new_lines', False))

            threads.append(thread)
            thread.start()

        selections.clear()
        self.handle_threads(edit, threads, selections, offset = 0, i = 0, dir = 1)

    def handle_threads(self, edit, threads, selections, offset = 0, i = 0, dir = 1):

        next_threads = []
        for thread in threads:
            if thread.is_alive():
                next_threads.append(thread)
                continue
            if thread.result == False:
                continue
            offset = self.replace(edit, thread, selections, offset)
        threads = next_threads

        if len(threads):
            before = i % 8
            after = (7) - before

            if not after:
                dir = -1
            if not before:
                dir = 1

            i += dir

            self.view.set_status('minify', '[%s=%s]' % (' ' * before, ' ' * after))

            sublime.set_timeout(lambda: self.handle_threads(edit, threads, selections, offset, i, dir), 100)
            return

        self.view.end_edit(edit)
        self.view.erase_status('minify')
        sublime.status_message('Successfully minified')

    def replace(self, edit, thread, selections, offset):

        sel = thread.sel
        original = thread.original
        result = thread.result

        if result is None:
            sublime.error_message("There was an error minifying the Javascript.")
            return

        editgroup = self.view.begin_edit('minify')

        if offset:
            sel = sublime.Region(sel.begin() + offset, sel.end() + offset)

        self.view.replace(edit, sel, result)

    def get_minifier(self, settings):
        compiler = settings.get('compiler', "google_closure")
        compilers = {
            'google_closure': GoogleClosureCall,
            'uglify_js': UglifyCall
        }

        return compilers[compiler] if compiler in compilers else compilers['google_closure']


