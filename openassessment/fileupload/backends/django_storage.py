import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage, get_storage_class
from django.core.urlresolvers import reverse_lazy

from .base import BaseBackend


class Backend(BaseBackend):
    """
    Manage openassessment student files uploaded using the default django storage settings.
    """

    # setup default backend storage provider as fallback if necessary
    backend_storage = default_storage

    # tracks if generated urls need to be expired
    expires = False

    def __init__(self, ora2_fileupload=None):
        """
        Initialize the backend storage class (if necessary)
        """

        # dynamically initialize the backend
        if 'STORAGE_CLASS' in ora2_fileupload and ora2_fileupload['STORAGE_CLASS']:
            expires = ora2_fileupload['STORAGE_KWARGS']['expires']
            storage_kwargs = ora2_fileupload['STORAGE_KWARGS']

            # get the backend provider & initialize it with override settings
            django_storages_backend_provider = get_storage_class(ora2_fileupload['STORAGE_CLASS'])
            self.backend_storage = django_storages_backend_provider(**storage_kwargs)

    def get_upload_url(self, key, content_type):
        """
        Return the URL pointing to the ORA2 django storage upload endpoint.
        """
        return reverse_lazy("openassessment-django-storage", kwargs={'key': key, 'content_type': self._encode_content_type(content_type)})

    def get_download_url(self, key):
        """
        Return the django storage download URL for the given key.

        Returns None if no file exists at that location.
        """
        path = self._get_file_path(key)
        if self.backend_storage.exists(path):
            return self.backend_storage.url(path, self.expires)
        return None

    def upload_file(self, key, content, content_type):
        """
        Upload the given file content to the keyed location.
        """
        path = self._get_file_path(key)

        # Azure defaults to application/octet-stream for blob. When content type is 
        # not explicitly set, the blob download link fails to open the file since the browser
        # cannot load application/octet-stream. Therefore, explicitly set the content type 
        # to the ContentFile object
        uploaded_file = ContentFile(content)
        uploaded_file.content_type = self._decode_content_type(content_type)
        saved_path = self.backend_storage.save(path, ContentFile(content))
        return saved_path

    def remove_file(self, key):
        """
        Remove the file at the given keyed location.

        Returns True if the file exists, and was removed.
        Returns False if the file does not exist, and so was not removed.
        """
        path = self._get_file_path(key)
        if self.backend_storage.exists(path):
            self.backend_storage.delete(path)
            return True
        return False

    def _encode_content_type(self, content_type):
        """
        Replace the content type separator with a placeholder

        Returns the encoded string
        """

        return content_type.replace("/", "__")

    def _decode_content_type(self, content_type):
        """
        Replace the content type placeholder with its original separator

        Returns the decoded string
        """

        return content_type.replace("__", "/")

    def _get_file_name(self, key):
        """
        Returns the name of the keyed file.

        Since the backend storage may be folders, or it may use pseudo-folders,
        make sure the filename doesn't include any path separators.
        """
        file_name = key.replace("..", "").strip("/ ")
        file_name = file_name.replace(os.sep, "_")
        return file_name

    def _get_file_path(self, key):
        """
        Returns the path to the keyed file, including the storage prefix.
        """
        path = self._get_key_name(self._get_file_name(key))
        return path
