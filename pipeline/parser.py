import re
import urllib.parse
from typing import Dict, Any, Optional
from monitoring.logger import get_logger

logger = get_logger("URLParser")

class URLParser:
    """
    Media URL normalization and cleanup pipeline component.
    Constitution Blueprint: Media URL preprocessing before validation.
    """

    def __init__(self):
        # Common URL cleanup patterns
        self.cleanup_patterns = [
            # Remove tracking parameters
            (r'[?&](utm_[^&]*|ref|source|campaign|medium)[&=][^&]*', ''),
            # Remove Facebook/Twitter tracking
            (r'[?&](fbclid|twclid)[^&]*', ''),
            # Remove YouTube timestamp tracking
            (r'[?&]t=\d+s?', ''),
            # Clean double slashes (except after protocol)
            (r'(?<!:)//+', '/'),
        ]

        # Known URL shorteners that should be expanded
        self.shorteners = {
            'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
            'buff.ly', 'adf.ly', 'is.gd', 'v.gd', 'tiny.cc'
        }

    def normalize_url(self, url: str) -> str:
        """
        Normalizes and cleans a media URL.
        Returns cleaned URL or original if cleaning fails.
        """
        if not url or not isinstance(url, str):
            return url

        try:
            # Parse URL
            parsed = urllib.parse.urlparse(url)

            # Validate scheme
            if parsed.scheme not in ['http', 'https']:
                logger.warning("Invalid URL scheme", extra={"context": {"url": url, "scheme": parsed.scheme}})
                return url

            # Reconstruct clean URL
            clean_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

            # Apply cleanup patterns
            for pattern, replacement in self.cleanup_patterns:
                clean_url = re.sub(pattern, replacement, clean_url, flags=re.IGNORECASE)

            # Remove trailing ? or & if no parameters remain
            clean_url = re.sub(r'[?&]$', '', clean_url)

            # Normalize domain to lowercase
            parsed_clean = urllib.parse.urlparse(clean_url)
            if parsed_clean.netloc:
                normalized_netloc = parsed_clean.netloc.lower()
                clean_url = clean_url.replace(parsed_clean.netloc, normalized_netloc)

            logger.debug("URL normalized", extra={"context": {"original": url, "cleaned": clean_url}})
            return clean_url

        except Exception as e:
            logger.warning("URL normalization failed", extra={"context": {"url": url, "error": str(e)}})
            return url

    def extract_media_info(self, url: str) -> Dict[str, Any]:
        """
        Extracts basic media information from URL for metadata enrichment.
        """
        info = {
            'original_url': url,
            'normalized_url': self.normalize_url(url),
            'domain': '',
            'path': '',
            'extension': '',
            'is_shortened': False,
            'likely_type': 'other'
        }

        try:
            parsed = urllib.parse.urlparse(info['normalized_url'])
            info['domain'] = parsed.netloc
            info['path'] = parsed.path

            # Check if shortened
            domain_parts = parsed.netloc.split('.')
            if len(domain_parts) >= 2:
                base_domain = '.'.join(domain_parts[-2:])
                info['is_shortened'] = base_domain in self.shorteners

            # Extract file extension
            if parsed.path:
                path_parts = parsed.path.split('/')
                filename = path_parts[-1] if path_parts else ''
                if '.' in filename:
                    info['extension'] = filename.split('.')[-1].lower()

            # Guess media type from extension
            video_exts = {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v'}
            audio_exts = {'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma'}
            image_exts = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'}

            if info['extension'] in video_exts:
                info['likely_type'] = 'video'
            elif info['extension'] in audio_exts:
                info['likely_type'] = 'audio'
            elif info['extension'] in image_exts:
                info['likely_type'] = 'image'

        except Exception as e:
            logger.warning("Media info extraction failed", extra={"context": {"url": url, "error": str(e)}})

        return info

    def validate_url_format(self, url: str) -> bool:
        """
        Basic URL format validation.
        """
        try:
            parsed = urllib.parse.urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False

def parse_media_url(url: str) -> Dict[str, Any]:
    """
    Convenience function for URL parsing.
    Returns normalized URL and extracted metadata.
    """
    parser = URLParser()
    return parser.extract_media_info(url)