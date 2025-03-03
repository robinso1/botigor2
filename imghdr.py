"""
Модуль imghdr для обеспечения совместимости с Python 3.13.
Этот модуль был удален из стандартной библиотеки Python 3.13.
"""

import os
import struct

def what(file, h=None):
    """
    Определяет тип изображения по содержимому файла.
    
    Args:
        file: Путь к файлу или файловый объект.
        h: Опционально, первые 32 байта файла.
    
    Returns:
        Строка с типом изображения или None, если тип не определен.
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
            
    for tf in tests:
        res = tf(h, file)
        if res:
            return res
    return None

def test_jpeg(h, f):
    """JPEG data in JFIF or Exif format"""
    if h[0:2] == b'\xff\xd8':
        return 'jpeg'

def test_png(h, f):
    """PNG data"""
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'

def test_gif(h, f):
    """GIF ('87 and '89 variants)"""
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'

def test_tiff(h, f):
    """TIFF data, big or little endian"""
    if h[:2] in (b'MM', b'II'):
        if h[2:4] == b'\x00\x2a':
            return 'tiff'

def test_webp(h, f):
    """WebP data"""
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'

tests = [
    test_jpeg,
    test_png,
    test_gif,
    test_tiff,
    test_webp,
] 