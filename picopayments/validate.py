from picopayments import db


def sync_input(handle, send_unused_revoke_secret_hash, sends, commit, revokes):
    # TODO validate input types/formats

    handles = [handle]
    if sends:
        [handles.append(send["handle"]) for send in sends]
    if not db.handles_exist(handles):
        msg = "One or more unknown handles: {0}"
        raise Exception(msg.format(repr(handles)))
