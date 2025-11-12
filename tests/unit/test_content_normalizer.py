import pytest
from bs4 import BeautifulSoup, Comment
from domain.content_normalizer import ContentNormalizer


@pytest.fixture
def sample_html() -> str:
    return """
    <html>
      <link href="/favicon.ico" rel="shortcut icon" type="image/x-icon" />
      <meta http-equiv="x-ua-compatible" content="ie=edge">
      <head>
        <style>.hidden {display:none;}</style>
        <script>console.log('test');</script>
      </head>
      <body class="main" id="body">
        <!-- This is a comment -->
        <nav>Navigation</nav>
        <footer>Footer</footer>
        <div class="content" style="color:red;">
          <p>   This   is   a   paragraph.   </p>
          <pre>   Preserve   whitespace   </pre>
          <code>   code   snippet   </code>
        </div>
      </body>
    </html>
    """


@pytest.fixture
def sample_divs() -> str:
    return """
    <html>
      <body>
        <div>
          <div>
            <div>
              <div>
                <div>
                  <p>This is content that is relevant</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """


@pytest.fixture
def sample_main() -> str:
    return """
    <html>
      <body>
        <div>
          <main role="main">
            <p>This is content that is relevant</p>
          </main>
          <div>
            other contents that are not relevant
          </div>
        </div>
      </body>
    </html>
    """


@pytest.fixture
def sample_empty_tags() -> str:
    return """
    <html>
      <body>
        <div>
          <main role="main">
            <p>This is content that is relevant</p>
            <p></p>
            <p>This is content that is relevant</p>
            <p></p>
            <center><strong></strong></center>
          </main>
          <div>
            other contents that are not relevant
          </div>
        </div>
      </body>
    </html>
    """


def test_normalize_removes_unwanted_tags_and_attributes(sample_html: str) -> None:
    normalizer = ContentNormalizer()
    normalized = normalizer.normalize(sample_html)
    soup = BeautifulSoup(normalized, "lxml")

    # Unwanted tags should be gone
    assert not soup.find("script")
    assert not soup.find("meta")
    assert not soup.find("link")
    assert not soup.find("title")
    assert not soup.find("style")
    assert not soup.find("nav")
    assert not soup.find("footer")

    # Attributes should be removed
    body = soup.find("body")
    assert body is not None
    assert not body.has_attr("class")
    assert not body.has_attr("id")

    div = soup.find("div")
    assert div is not None
    assert not div.has_attr("class")
    assert not div.has_attr("style")

    # Comments should be removed
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    assert len(comments) == 0


def test_whitespace_normalization(sample_html: str) -> None:
    normalizer = ContentNormalizer()
    normalized = normalizer.normalize(sample_html)
    soup = BeautifulSoup(normalized, "lxml")
    p = soup.find("p")
    # Text should be collapsed to single spaces and stripped
    assert p is not None
    assert p.get_text() == "This is a paragraph."


def test_pre_and_code_preserve_whitespace(sample_html: str) -> None:
    normalizer = ContentNormalizer()
    normalized = normalizer.normalize(sample_html)
    soup = BeautifulSoup(normalized, "lxml")
    pre = soup.find("pre")
    assert pre is not None
    code = soup.find("code")
    assert code is not None
    # Whitespace inside pre and code should be preserved (including leading/trailing spaces)
    assert pre.get_text() == "   Preserve   whitespace   "
    assert code.get_text() == "   code   snippet   "


def test_remove_nested_divs(sample_divs: str) -> None:
    html = """
    <html>
      <body>
        <div>
          <p>This is content that is relevant</p>
        </div>
      </body>
    </html>
    """
    expected_html = BeautifulSoup(html, "lxml").prettify()

    normalizer = ContentNormalizer()
    normalized = normalizer.normalize(sample_divs)
    soup = BeautifulSoup(normalized, "lxml")
    assert soup.prettify() == expected_html


def test_just_keep_role_main(sample_main: str) -> None:
    html = """
    <html>
      <body>
        <main role="main">
          <p>This is content that is relevant</p>
        </main>
      </body>
    </html>
    """
    expected_html = BeautifulSoup(html, "lxml").prettify()

    normalizer = ContentNormalizer()
    normalized = normalizer.normalize(sample_main)
    soup = BeautifulSoup(normalized, "lxml")
    assert soup.prettify() == expected_html


def test_remove_empty_tags(sample_empty_tags: str) -> None:
    html = """
    <html>
      <body>
        <main role="main">
          <p>This is content that is relevant</p>
          <p>This is content that is relevant</p>
        </main>
      </body>
    </html>
    """
    expected_html = BeautifulSoup(html, "lxml").prettify()

    normalizer = ContentNormalizer()
    normalized = normalizer.normalize(sample_empty_tags)
    soup = BeautifulSoup(normalized, "lxml")
    assert soup.prettify() == expected_html
