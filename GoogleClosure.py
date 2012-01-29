import sublime, sublime_plugin
from GoogleClosureCall import GoogleClosureCall

class Minify(sublime_plugin.TextCommand):
    def run(self, edit):

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

        threads = []
        for sel in selections:
            selbody = self.view.substr(sel)
            thread = GoogleClosureCall(sel, selbody, 5)
            threads.append(thread)
            thread.start()

        selections.clear()
        editgroup = self.view.begin_edit('minify')
        self.handle_threads(edit, threads, selections, offset = 0, i = 0, dir = 1)

    def handle_threads(self, edit, threads, selections, offset = 0, i = 0, dir = 1):
        print "handling threads"
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

        editgroup = self.view.begin_edit('minify')

        if offset:
            sel = sublime.Region(sel.begin() + offset, sel.end() + offset)

        self.view.replace(edit, sel, result)
