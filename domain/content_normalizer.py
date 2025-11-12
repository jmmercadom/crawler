from bs4 import BeautifulSoup, Comment
from bs4 import Tag


class ContentNormalizer:
    """Normalizes HTML content to extract semantic structure."""

    def normalize(self, html_content: str) -> str:
        """
        Create distilled version of the HTML content.

        The method now delegates each processing stage to a dedicated
        helper, making the flow easier to understand and extend.
        """
        soup = BeautifulSoup(html_content, "lxml")
        soup = self._remove_unwanted_tags(soup)
        soup = self._strip_tag_attributes(soup)
        soup = self._remove_comments(soup)
        soup = self._collapse_nested_divs(soup)
        soup = self._handle_main_tag(soup)
        soup = self._normalize_text_nodes(soup)
        soup = self._preserve_pre_code_whitespace(soup)
        soup = self._remove_empty_tags(soup)
        return str(soup)

    def _remove_unwanted_tags(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove script, style, nav, footer, link, meta, and title tags."""
        for tag in soup.find_all(
            ["script", "style", "nav", "footer", "link", "meta", "title"]
        ):
            tag.decompose()
        return soup

    def _strip_tag_attributes(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Delete class, style, and id attributes from all remaining tags."""
        for tag in soup.find_all(True):
            for attr in ["class", "style", "id"]:
                if attr in tag.attrs:
                    del tag.attrs[attr]
        return soup

    def _remove_comments(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract all HTML comments."""
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        return soup

    def _collapse_nested_divs(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Repeatedly unwrap inner <div> tags when a parent <div> contains
        exactly one <div> child.
        """
        while True:
            changed = False
            for div in soup.find_all("div"):
                child_tags = [c for c in div.contents if isinstance(c, Tag)]
                if len(child_tags) == 1 and child_tags[0].name == "div":
                    child_tags[0].unwrap()
                    changed = True
            if not changed:
                break
        return soup

    def _handle_main_tag(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        If a <main role="main"> element exists, keep only it and discard
        other body content.
        """
        main_tag = soup.find("main", attrs={"role": "main"})
        if main_tag:
            main_tag.extract()
            body_tag = soup.find("body")
            if body_tag:
                body_tag.clear()
                body_tag.append(main_tag)
        return soup

    def _normalize_text_nodes(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Collapse whitespace in text nodes (excluding <pre> and <code>),
        and remove nodes that contain only whitespace.
        """
        for text_node in soup.find_all(string=True):
            parent = text_node.parent
            if parent and parent.name not in ["pre", "code"]:
                if text_node.strip() == "":
                    text_node.extract()
                else:
                    collapsed = " ".join(text_node.split())
                    text_node.replace_with(collapsed)
        return soup

    def _preserve_pre_code_whitespace(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Preserve whitespace inside <pre> and <code> tags but strip
        surrounding newline characters.
        """
        for tag in soup.find_all(["pre", "code"]):
            for txt in tag.find_all(string=True):
                cleaned = txt.strip("\n")
                txt.replace_with(cleaned)
        return soup

    def _remove_empty_tags(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Iteratively delete tags whose text content is empty after
        stripping whitespace. This also removes tags that only contain
        other empty tags.
        """
        while True:
            removed = False
            for tag in list(soup.find_all(True)):
                if tag.get_text(strip=True) == "":
                    tag.decompose()
                    removed = True
            if not removed:
                break
        return soup
