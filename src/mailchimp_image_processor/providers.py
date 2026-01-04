import os
from abc import ABC, abstractmethod
from PIL import Image as img, UnidentifiedImageError
from PIL.Image import Image


class ImageProvider(ABC):
    @abstractmethod
    def extract(self, source: str) -> list[Image]:
        pass


class Filesystem(ImageProvider):
    def extract(self, source: str) -> list[Image]:
        """Read one or more images from the given path.

        If source is a file, try to read it as an PIL.Image and return an array with just that item.
        If source is a directory, load all image files in the directory as PIL.Image and return an array with the images. Does NOT descend into subdirectories.
        """
        if os.path.isfile(source):
            return [self._extract_from_file(source)]
        elif os.path.isdir(source):
            return self._extract_from_dir(source)
        else:
            raise ValueError("`source` must be the path to a file or directory.")

    def _extract_from_dir(self, directory: str) -> list[Image]:
        images: list[Image] = []
        for file in os.listdir(directory):
            try:
                images.append(self._extract_from_file(os.path.join(directory, file)))
            except UnidentifiedImageError:
                # Ignore unreadable files. Potentially display warning.
                pass
        return images

    def _extract_from_file(self, file: str) -> Image:
        return img.open(file)
