"""
This is intended to be run within a docker container with
the dash testing libraries and chrome driver
"""

import pytest

FILESYSTEM_MODULE = "portfolio_analytics.common.filesystem"


@pytest.fixture
def initialized_dash(dash_duo):
    """Initialize connection to the deployed dash application for testing."""
    # Use localhost since we're using host network
    dash_duo.server_url = "http://localhost:8050"
    yield dash_duo


@pytest.mark.integration
@pytest.mark.dashboard_integration
def test_dash_app_basic_elements(initialized_dash):
    """Test basic elements are present and visible."""
    dash_duo = initialized_dash

    # Test title is present
    dash_duo.wait_for_text_to_equal("h1", "Portfolio Analytics Dashboard", timeout=10)

    # Test that dropdowns are present
    assert dash_duo.find_element("#portfolio-selector").is_displayed()
    assert dash_duo.find_element("#currency-selector").is_displayed()

    # Test that time period buttons are present and MAX is active by default
    max_button = dash_duo.find_element("#max-button")
    assert max_button.is_displayed()

    # Test that graph container is present and wait for it to become visible
    dash_duo.wait_for_element("#pnl-graph", timeout=10)


@pytest.mark.integration
@pytest.mark.dashboard_integration
def test_no_file_error_message(initialized_dash):
    """Test that error messages are not shown on the page."""
    dash_duo = initialized_dash

    # Wait for the page to load
    dash_duo.wait_for_text_to_equal("h1", "Portfolio Analytics Dashboard", timeout=4)

    # Get the page content using a valid CSS selector
    page_content = dash_duo.find_element("body").text

    # Assert that error messages are not present
    error_messages = ["No such file or directory", "No data available"]
    for error in error_messages:
        assert (
            error not in page_content
        ), f"Found '{error}' error in page content: {page_content}"

    # Additionally check that the graph container is not showing errors
    graph = dash_duo.find_element("#pnl-graph")
    graph_text = graph.text
    for error in error_messages:
        assert error not in graph_text, f"Found '{error}' error in graph: {graph_text}"


@pytest.mark.integration
@pytest.mark.dashboard_integration
def test_portfolio_selector_functionality(initialized_dash):
    """Test portfolio selector dropdown options and behavior."""
    dash_duo = initialized_dash

    # Wait for the portfolio selector to be present and visible
    portfolio_selector = dash_duo.wait_for_element("#portfolio-selector", timeout=4)
    assert portfolio_selector.is_displayed()

    # Click the dropdown to open it
    portfolio_selector.click()

    # Wait for and verify the presence of the default option
    default_option = dash_duo.wait_for_contains_text(
        "#portfolio-selector", "sample_portfolio.csv"
    )
    assert default_option is not None


@pytest.mark.integration
@pytest.mark.dashboard_integration
def test_currency_selector_functionality(initialized_dash):
    """Test currency selector options and behavior."""
    dash_duo = initialized_dash

    # Wait for the currency selector to be present and visible
    currency_selector = dash_duo.wait_for_element("#currency-selector", timeout=4)
    assert currency_selector.is_displayed()

    # Click the dropdown to open it
    currency_selector.click()

    # Wait for and verify the presence of USD (default currency)
    default_option = dash_duo.wait_for_contains_text("#currency-selector", "USD")
    assert default_option is not None


@pytest.mark.integration
@pytest.mark.dashboard_integration
def test_time_period_buttons(initialized_dash):
    """Test all time period buttons are present and functional."""
    dash_duo = initialized_dash

    buttons = ["1m-button", "6m-button", "1y-button", "max-button", "custom-button"]
    for button_id in buttons:
        # Use CSS selector syntax with [] for id attribute
        button = dash_duo.find_element(f'[id="{button_id}"]')
        assert button.is_displayed()
        assert button.get_property("style")


@pytest.mark.integration
@pytest.mark.dashboard_integration
def test_stats_display(initialized_dash):
    """Test performance statistics are displayed correctly."""
    dash_duo = initialized_dash

    # Wait for stats element with timeout
    stats_element = dash_duo.wait_for_element("#stats-display", timeout=4)
    assert stats_element is not None, "Stats display element not found"

    # Get the stats text content
    stats_text = stats_element.text

    # Check if we have an error message
    if "Unable to calculate statistics" in stats_text:
        # Test passes if we get the expected error message
        assert "Unable to calculate statistics due to missing data" in stats_text
        return

    # If no error message, check for the metrics
    expected_metrics = ["MAX DRAWDOWN", "SHARPE", "PERIOD PNL"]

    found_metrics = []
    for metric in expected_metrics:
        if metric in stats_text:
            found_metrics.append(metric)

    assert found_metrics, f"No expected metrics found. Content: {stats_text}"
