from couchdb.design import ViewDefinition
from django.conf import settings
from django.db.models import signals
import djcouch
import re
from textwrap import dedent

section_division_re = re.compile(r'^\s*/////+\s*$', re.M)
view_naming_re = re.compile(r'^(\w+\.)?(\w+)\s*=\s*(function.+)$', re.S)

def parse_couchdb_views(func_name, doc, views, verbosity):
    for section in section_division_re.split(doc):
        m = view_naming_re.match(section.strip())
        if not m:
            continue
        db_name, view_name, code = m.groups()
        db_name = djcouch.DEFAULT_DATABASE if not db_name else db_name[:-1]
        assert db_name in djcouch.DATABASE_NAMES, ("No such CouchDB "
                "database '%s' in function %s" % (db_name, func_name))
        design_doc = db_name + djcouch.DESIGN_DOC_SUFFIX
        view_def = ViewDefinition(design_doc, view_name, code.strip())
        db_views = views.setdefault(db_name, [])
        db_views.append(view_def)
        if verbosity:
            print 'Found view %s.%s in %s' % (db_name, view_name, func_name)

def create_couchdb_views(app, created_models, verbosity, **kwargs):
    """Searches each installed app's views.py for CouchDB
    view functions in view functions' docstrings."""
    views = {}
    if verbosity:
        print 'Searching for CouchDB views...'
    for app_name in settings.INSTALLED_APPS:
        try:
            mod = __import__(app_name, globals(), locals(), ['views'])
        except ImportError:
            continue
        try:
            for sym in dir(mod.views):
                obj = getattr(mod.views, sym, None)
                name = getattr(obj, '__name__', None)
                doc = getattr(obj, '__doc__', None)
                if name and doc:
                    parse_couchdb_views(name, dedent(doc), views, verbosity)
        except AttributeError:
            pass
    if views:
        if verbosity:
            print 'Synching CouchDB views.'
        for db_name, db_views in views.iteritems():
            ViewDefinition.sync_many(djcouch.dbs[db_name], db_views)
    elif verbosity:
        print 'No CouchDB views found.'

signals.post_syncdb.connect(create_couchdb_views, sender=djcouch.models)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
