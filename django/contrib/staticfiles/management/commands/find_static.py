import os
from optparse import make_option
from django.core.management.base import LabelCommand

from django.contrib.staticfiles import finders

class Command(LabelCommand):
    help = "Finds the absolute paths for the given static file(s)."
    args = "[static_file ...]"
    label = 'static file'
    option_list = LabelCommand.option_list + (
        make_option('--first', action='store_false', dest='all', default=True,
                    help="Only return the first match for each static file."),
    )

    def handle_label(self, media_path, **options):
        logger = self.get_logger()
        all = options['all']
        result = finders.find(media_path, all=all)
        if not result:
            logger.warning("No matching file found for %r." % media_path)
            return
        output = '\n  '.join((os.path.realpath(path) for path in result))
        logger.info("Found %r here:\n  %s" % (media_path, output))
