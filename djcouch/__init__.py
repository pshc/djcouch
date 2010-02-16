import couchdb
from couchdb.http import ResourceNotFound, PreconditionFailed
from django.conf import settings
from django.http import Http404

class CouchDBImproperlyConfigured(Exception):
    pass

try:
    HOST = settings.COUCHDB_HOST
except AttributeError:
    raise CouchDBImproperlyConfigured("Please ensure that COUCHDB_HOST is "
            "set in your settings file.")

def _determine_db_name():
    id = getattr(settings, 'COUCHDB_DATABASE_NAME', None)
    if not id:
        id = getattr(settings, 'SITE_PREFIX', None)
        if not id:
            raise CouchDBImproperlyConfigured("Couldn't determine a default "
                    "database name; please set COUCHDB_DATABASE_NAME "
                    "in your settings.")
    return id

DATABASE_NAME = _determine_db_name()
DESIGN_DOCNAME = getattr(settings, 'COUCHDB_DESIGN_DOCNAME',
                         DATABASE_NAME + '-design')

if not hasattr(settings, 'couchdb_server'):
    settings.couchdb_server = couchdb.client.Server(HOST)
server = settings.couchdb_server

if not hasattr(settings, 'couchdb_db'):
    try:
        settings.couchdb_db = server.create(DATABASE_NAME)
    except PreconditionFailed as e:
        if 'file_exists' not in str(e):
            raise
        settings.couchdb_db = server[DATABASE_NAME]
db = settings.couchdb_db

def view(name, empty_ok=True, **kwargs):
    """Wraps db.view(...) with convenience functionality.

    Prepends $DESIGN_DOCNAME/ to the given view name.
    If Django view foo() has a docstring containing a CouchDB view bar,
    you should pass "foo.bar" as the view name.

    If keyword argument empty_ok=True (the default), swallows the
    ('not_found', 'missing') exception if no results are returned.
    """
    name = '%s/%s' % (DESIGN_DOCNAME, name)
    if empty_ok:
        return _view_empty_ok(name, **kwargs)
    return db.view(name, **kwargs)

# Stupid hack
def _view_empty_ok(name, **kwargs):
    try:
        for obj in db.view(name, **kwargs):
            yield obj
    except ResourceNotFound as e:
        if 'missing' in str(e):
            raise StopIteration
        else:
            raise

def get_document_or_404(id):
    """Like get_object_or_404; raises Http404 if the document doesn't exist."""
    try:
        return db[id]
    except ResourceNotFound:
        raise Http404

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
