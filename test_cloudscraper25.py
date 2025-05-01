import cloudscraper25

# Create a scraper instance
scraper = cloudscraper25.create_scraper(browser='chrome')

# Print the version
print(f"Using cloudscraper25 version: {cloudscraper25.__version__}")

# Make a simple request to a non-Cloudflare site to test
response = scraper.get('https://httpbin.org/get')
print(f"Response status code: {response.status_code}")
print(f"Response content: {response.text[:200]}...")  # Print first 200 chars
