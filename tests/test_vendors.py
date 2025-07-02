from nidus_scraper.vendors import extract_pdfs


def test_extract_pdfs_relative():
    html = '<a href="docs\\file.pdf">PDF</a>'
    urls = list(extract_pdfs(html, 'https://example.com/base/'))
    assert urls == ['https://example.com/base/docs/file.pdf']
