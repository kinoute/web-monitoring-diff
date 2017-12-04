from bs4 import BeautifulSoup
from .html_diff_render import diff_elements, get_title


def links_diff(a_text, b_text):
    """
    Extracts all the outgoing links from a page and produces a diff of an
    HTML document that is simply a list of the text and URL of those links.

    It ignores links that merely navigate within the page.

    NOTE: this diff currently suffers from the fact that our diff server does
    not know the original URL of the content, so it can identify:
        <a href="#anchor-in-this-page">Text</a>
    as an internal link, but not:
        <a href="http://this.domain.com/this/page#anchor-in-this-page">Text</a>
    """
    soup_old = BeautifulSoup(a_text, 'lxml')
    soup_new = BeautifulSoup(b_text, 'lxml')

    old_links = _create_link_soup(soup_old)
    new_links = _create_link_soup(soup_new)

    new_links.body.replace_with(diff_elements(old_links.body, new_links.body))

    change_styles = new_links.new_tag(
        'style',
        type='text/css',
        id='wm-diff-style')
    change_styles.string = """
        ins {text-decoration: none; background-color: #d4fcbc;}
        del {text-decoration: none; background-color: #fbb6c2;}"""
    new_links.head.append(change_styles)

    return new_links.prettify(formatter=None)


def _find_outgoing_links(soup):
    """
    Yields each of the `<a>` elements in a Beautiful Soup document that point
    to other pages.
    """
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and not href.startswith('#'):
            yield link


def _create_empty_soup(title=''):
    """
    Creates a Beautiful Soup document representing an empty HTML page.

    Parameters
    ----------
    title : string
        The new document's title.
    """
    return BeautifulSoup(f"""<!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
            </head>
            <body>
            </body>
        </html>
        """, 'lxml')


def _create_link_soup(source_soup):
    listings = [_create_link_listing(link, source_soup)
                for link in _find_outgoing_links(source_soup)]
    link_set = sorted(set(listings), key=lambda listing: listing.text.lower())

    result = _create_empty_soup(get_title(source_soup))
    result_list = result.new_tag('ul')
    result.body.append(result_list)
    for item in link_set:
        result_list.append(item)

    return result


def _create_link_listing(link, soup):
    """
    Create an element to display in the list of links.
    """
    listing = soup.new_tag('li')
    listing.append(f'{link.text} ')

    url = link['href']
    url_link = soup.new_tag('a', href=url)
    url_link.string = f'({url})'
    listing.append(url_link)
    return listing
