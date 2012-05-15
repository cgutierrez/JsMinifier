from os import path

import sublime
import sublime_plugin

from compilers import GoogleClosureCall, UglifyCall

class BaseMinifier(sublime_plugin.TextCommand):
    """Base Minifier"""

    def __init__(self, view):
        self.view = view
        self.window = sublime.active_window()
        self.settings = sublime.load_settings("Minifier.sublime-settings")

    def run(self, edit):

        selections = self.get_selections()
        CompilerCall = self.get_minifier()

        threads = []
        for sel in selections:
            selbody = self.view.substr(sel)

            thread = CompilerCall(
                        sel,
                        selbody,
                        timeout=5,
                        level=self.settings.get('optimization_level', "WHITESPACE_ONLY"),
                        rm_new_lines=self.settings.get('remove_new_lines', False))

            threads.append(thread)
            thread.start()

        selections.clear()
        self.handle_threads(edit, threads, selections, offset=0, i=0, dir=1)

    def get_selections(self):
        selections = self.view.sel()

        # check if the user has any actual selections
        has_selections = False
        for sel in selections:
            if sel.empty() == False:
                has_selections = True

        # if not, add the entire file as a selection
        if not has_selections:
            full_region = sublime.Region(0, self.view.size())
            selections.add(full_region)

        return selections

    def handle_threads(self, edit, threads, selections, offset = 0, i = 0, dir = 1):

        next_threads = []
        for thread in threads:
            if thread.is_alive():
                next_threads.append(thread)
                continue
            if thread.result == False:
                continue
            self.handle_result(edit, thread, selections, offset)
        threads = next_threads

        if len(threads):
            before = i % 8
            after = (7) - before

            dir = -1 if not after else dir
            dir = 1 if not before else dir

            i += dir

            self.view.set_status('minify', '[%s=%s]' % (' ' * before, ' ' * after))

            sublime.set_timeout(lambda: self.handle_threads(edit, threads, selections, offset, i, dir), 100)
            return

        self.view.end_edit(edit)
        self.view.erase_status('minify')
        sublime.status_message('Successfully minified')

    def handle_result(self, edit, thread, selections, offset):
        sel = thread.sel
        original = thread.original
        result = thread.result

        if thread.error is True:
            sublime.error_message(result)
            return
        elif result is None:
            sublime.error_message("There was an error minifying the Javascript.")
            return

        return thread

    def get_minifier(self):
        compiler = self.settings.get('compiler', "google_closure")
        compilers = {
            'google_closure': GoogleClosureCall,
            'uglify_js': UglifyCall
        }

        return compilers[compiler] if compiler in compilers else compilers['google_closure']

    def get_new_line(self):
        CR = chr(0x0D)
        LF = chr(0x0A)
        endtypes = {'u': LF, 'w': CR+LF, 'm': CR}
        return endtypes[self.view.line_endings()[0].lower()]


class Minify(BaseMinifier):

    def handle_result(self, edit, thread, selections, offset):
        result = super(Minify, self).handle_result(edit, thread, selections, offset)

        editgroup = self.view.begin_edit('minify')

        sel = thread.sel
        result = thread.result
        if offset:
            sel = sublime.Region(thread.sel.begin() + offset, thread.sel.end() + offset)

        self.view.replace(edit, sel, result)

class MinifyToFile(BaseMinifier):

    def run(self, edit):

        self.selections_completed = 0
        self.output = ""
        self.total_selections = len(self.get_selections())

        super(MinifyToFile, self).run(edit)

    def handle_result(self, edit, thread, selections, offset):

        self.selections_completed += 1

        super(MinifyToFile, self).handle_result(edit, thread, selections, offset)

        self.output = self.output + self.get_new_line() + thread.result

        # test if all the selections have been minified. if so, write all the output to the new file
        if self.selections_completed is self.total_selections:

            current_file = self.view.file_name()

            file_parts = path.splitext(current_file)
            min_file_suffix = self.settings.get('min_file_suffix', '.min')

            file_name = file_parts[0] + min_file_suffix + file_parts[1]

            file_path = path.join(
                path.dirname(current_file),
                file_name
            )
            
            with open(file_path, 'w+', 0) as min_file:
                min_file.write(self.output.strip())
            
            print self.settings.get('open_on_min', True)
            if (self.settings.get('open_on_min', True) == True):
                self.window.open_file(file_name)