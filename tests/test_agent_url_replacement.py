import pytest
from unittest.mock import MagicMock
from browser_use.agent.service import Agent

class TestAgentUrlReplacement:
    @pytest.fixture
    def mock_agent(self):
        agent = MagicMock()
        # Bind the method to the mock agent so it can be called as if it were an instance method
        # Setting the limit to 25 chars for the query/fragment part
        agent._url_shortening_limit = 25
        return agent

    def test_no_urls(self, mock_agent):
        """Test that text without URLs remains unchanged."""
        text = "This is a text with no URLs."
        new_text, replaced_urls = Agent._replace_urls_in_text(mock_agent, text)
        assert new_text == text
        assert replaced_urls == {}

    def test_short_url(self, mock_agent):
        """Test that a short URL is not replaced."""
        text = "Check this https://short.com"
        new_text, replaced_urls = Agent._replace_urls_in_text(mock_agent, text)
        assert new_text == text
        assert replaced_urls == {}

    def test_long_path_no_query(self, mock_agent):
        """Test that a long URL path without query/fragment is NOT replaced (based on current implementation)."""
        # This implementation only shortens the query/fragment part
        long_url = "https://example.com/very/long/path/that/is/definitely/longer/than/25/chars"
        text = f"Check {long_url}"

        new_text, replaced_urls = Agent._replace_urls_in_text(mock_agent, text)

        assert new_text == text
        assert replaced_urls == {}

    def test_long_url_with_query(self, mock_agent):
        """Test that a URL with a long query string is replaced."""
        base_url = "https://example.com/path"
        # Query length > 25
        query = "?query=verylongparamthatisdefinitelylongerthan25chars"
        long_url = f"{base_url}{query}"
        text = f"Check this {long_url}"

        new_text, replaced_urls = Agent._replace_urls_in_text(mock_agent, text)

        assert new_text != text
        assert len(replaced_urls) == 1
        assert long_url in replaced_urls.values()

        shortened_url = list(replaced_urls.keys())[0]
        # Verify base URL is preserved
        assert base_url in shortened_url
        # Verify it was shortened
        assert len(shortened_url) < len(long_url)
        # Verify hash was added
        assert "..." in shortened_url

    def test_long_url_with_fragment(self, mock_agent):
        """Test that a URL with a long fragment is replaced."""
        base_url = "https://example.com/path"
        fragment = "#fragment=verylongfragmentthatisdefinitelylongerthan25chars"
        long_url = f"{base_url}{fragment}"
        text = f"Check this {long_url}"

        new_text, replaced_urls = Agent._replace_urls_in_text(mock_agent, text)

        assert new_text != text
        assert len(replaced_urls) == 1
        assert long_url in replaced_urls.values()

    def test_multiple_urls(self, mock_agent):
        """Test replacement of multiple URLs in the same text."""
        short_url = "https://short.com"
        long_query_url = "https://example.com/path?q=verylongquerythatisdefinitelylongerthan25chars"
        text = f"Here is {short_url} and {long_query_url}"

        new_text, replaced_urls = Agent._replace_urls_in_text(mock_agent, text)

        # Short URL should remain
        assert short_url in new_text
        # Long URL should be replaced
        assert long_query_url not in new_text

        assert len(replaced_urls) == 1
        assert list(replaced_urls.values())[0] == long_query_url

    def test_empty_string(self, mock_agent):
        """Test that empty string returns empty string."""
        text = ""
        new_text, replaced_urls = Agent._replace_urls_in_text(mock_agent, text)
        assert new_text == ""
        assert replaced_urls == {}

    def test_url_exact_limit(self, mock_agent):
        """Test boundary condition where query/fragment is exactly the limit."""
        mock_agent._url_shortening_limit = 5
        base = "https://ex.com"

        # Case 1: Exceeds limit AND overhead (overhead is ~10 chars: 3 for '...' + 7 for hash)
        # Shortened = base + limit(5) + 10 = base + 15
        # Original must be > base + 15
        query_long = "?1234567890123456" # len 17
        url_long = base + query_long
        new_text_long, replaced_urls_long = Agent._replace_urls_in_text(mock_agent, url_long)
        assert new_text_long != url_long

        # Case 2: Within limit (exact)
        query_exact = "?1234" # len 5
        url_exact = base + query_exact
        new_text_exact, replaced_urls_exact = Agent._replace_urls_in_text(mock_agent, url_exact)
        assert new_text_exact == url_exact
        assert replaced_urls_exact == {}
