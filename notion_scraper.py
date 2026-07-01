import csv
from playwright.sync_api import sync_playwright

def extract_table_data(page, data_dict, headers):
    """Extracts visible cells mapped exactly to columns and resolves full URLs."""
    rows = page.locator(".notion-table-view .notion-collection-item").all()
    for row in rows:
        row_id = row.get_attribute("data-block-id")
        if row_id and row_id not in data_dict:
            cells = row.locator(".notion-table-view-cell").all()
            if len(cells) == len(headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    link = cell.locator("a").first
                    val = link.get_attribute("href") if link.count() > 0 else cell.inner_text().strip().replace('\n', ' ')
                    row_data[headers[i]] = val
                data_dict[row_id] = row_data

url = "https://dear-wasabi-26c.notion.site/f62e3291fad34c29b6161c38d610421a?v=3f013c94cd844cc99bc230063144427a"
output_file = "research_internships_database.csv"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 15000, "height": 1000})
    page = context.new_page()
    page.goto(url)
    page.wait_for_selector(".notion-table-view .notion-collection-item", timeout=15000)
    
    header_locators = page.locator(".notion-table-view-header-cell").all()
    headers = [h.inner_text().strip().replace('\n', ' ') for h in header_locators]
    
    data_dict = {}
    scroller = page.locator(".notion-scroller").first
    retries = 0
    
    while retries < 5:
        prev_count = len(data_dict)
        extract_table_data(page, data_dict, headers)
        
        scroller.evaluate("node => node.scrollBy(0, 1000)")
        page.wait_for_timeout(1000)
        
        if len(data_dict) == prev_count:
            retries += 1
        else:
            retries = 0

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row_data in data_dict.values():
            writer.writerow(row_data)
            
    browser.close()