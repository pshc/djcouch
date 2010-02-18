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

try:
    DATABASE_NAMES = settings.COUCHDB_DATABASES
except AttributeError:
    raise CouchDBImproperlyConfigured("Please ensure that "
            "COUCHDB_DATABASES is set in your settings file.")
if not isinstance(DATABASE_NAMES, (list, tuple)):
    raise CouchDBImproperlyConfigured("COUCHDB_DATABASES must be a list "
            "of database names.")

DEFAULT_DATABASE = getattr(settings, 'COUCHDB_DEFAULT_DATABASE', None)

DESIGN_DOC_SUFFIX = getattr(settings, 'COUCHDB_DESIGN_DOC_SUFFIX', '-design')

if not hasattr(settings, 'couchdb_server'):
    settings.couchdb_server = couchdb.client.Server(HOST)
server = settings.couchdb_server

if not hasattr(settings, 'couchdb_dbs'):
    settings.couchdb_dbs = {}
    for _name in DATABASE_NAMES:
        try:
            _db = server.create(_name)
        except PreconditionFailed as _e:
            if 'file_exists' not in str(_e):
                raise
            _db = server[_name]
        settings.couchdb_dbs[_name] = _db
dbs = settings.couchdb_dbs

def view(view_name, db=None, empty_ok=True, **kwargs):
    """Wraps db.view(...) with convenience functionality.

    If keyword argument empty_ok=True (the default), swallows the
    ('not_found', 'missing') exception if no results are returned.
    """
    db_name = DEFAULT_DATABASE if db is None else db
    db = dbs[db_name]
    name = '%s%s/%s' % (db_name, DESIGN_DOC_SUFFIX, view_name)
    if empty_ok:
        return _view_empty_ok(db, name, kwargs)
    return db.view(name, **kwargs)

# Stupid hack
def _view_empty_ok(db, name, kwargs):
    try:
        for obj in db.view(name, **kwargs):
            yield obj
    except ResourceNotFound as e:
        if 'missing' in str(e):
            raise StopIteration
        else:
            raise

def get_document_or_404(id, db=None):
    """Like get_object_or_404; raises Http404 if the document doesn't exist."""
    try:
        return dbs[DEFAULT_DATABASE if db is None else db][id]
    except ResourceNotFound:
        raise Http404

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
