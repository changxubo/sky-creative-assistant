# Copyright (c) 2025 Sky Creative Assistant
# SPDX-License-Identifier: MIT

import pytest
from src.tools.web_crawler import WebCrawler


def test_crawler_initialization():
    """Test that crawler can be properly initialized."""
    crawler = WebCrawler()
    assert isinstance(crawler, WebCrawler)


def test_crawler_crawl_valid_url():
    """Test crawling with a valid URL."""
    crawler = WebCrawler()
    test_url = "https://finance.sina.com.cn/stock/relnews/us/2024-08-15/doc-incitsya6536375.shtml"
    result = crawler.crawl(test_url)
    assert result is not None
    assert hasattr(result, "to_markdown")


def test_crawler_markdown_output():
    """Test that crawler output can be converted to markdown."""
    crawler = WebCrawler()
    test_url = "https://finance.sina.com.cn/stock/relnews/us/2024-08-15/doc-incitsya6536375.shtml"
    result = crawler.crawl(test_url)
    markdown = result.to_markdown()
    assert isinstance(markdown, str)
    assert len(markdown) > 0
