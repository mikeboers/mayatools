from __future__ import absolute_import

import contextlib
import functools
import os
import traceback

from maya import cmds, mel
import maya.utils

try:
    import sgactions.ticketui
except ImportError:
    sgactions = None


_registered = False
def register_hook():
    global _registered
    _registered = True
    maya.utils._guiExceptHook = _exception_hook


# Somewhere to store our state.
exceptions = []


def _exception_hook(exc_type, exc_value, exc_traceback, detail=2):
    exceptions.append((exc_type, exc_value, exc_traceback))
    try:
        return maya.utils.formatGuiException(exc_type, exc_value, exc_traceback, detail)
    except:
        return '# '.join(traceback.format_exception(exc_type, exc_value, exc_traceback)).rstrip()


# Our own brand of the ticket UI.
if sgactions:

    class Dialog(sgactions.ticketui.Dialog):

        def _get_reply_data(self, exc_info):

            data = [
                ('User Comment', str(self._description.toPlainText())),
                ('Maya Context', {
                    'file': cmds.file(q=True, expandName=True),
                    'workspace': cmds.workspace(q=True, rootDirectory=True),
                    'version': int(mel.eval('about -version').split()[0]),
                }),
                ('Maya Selection', cmds.ls(sl=True)),
                ('Maya References', cmds.file(q=True, reference=True)),
            ]
            if exc_info:
                data.append(('Traceback', exc_info))
            data.append(('OS Environment', dict(os.environ)))
            return data

    ticket_ui_context = functools.partial(sgactions.ticketui.ticket_ui_context, dialog_class=Dialog)

else:
    @contextlib.contextmanager
    def ticket_ui_context():
        yield


# Cleanup the submit dialog on autoreload.
dialog = None
def __before_reload__():
    global dialog
    if dialog:
        dialog.close()
        dialog.destroy()
    return _registered, exceptions

def __after_reload__(state=None):
    if state:
        registered, old_exceptions = state
        if registered:
            register_hook()
        exceptions.extend(old_exceptions)


def run_submit_ticket():
    global dialog
    if dialog:
        dialog.close()
    dialog = Dialog(exceptions=exceptions)
    dialog.show()


