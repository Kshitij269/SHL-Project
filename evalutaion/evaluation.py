import requests
from bs4 import BeautifulSoup
import json
import time

# Original data
products = [
    {
        "name": "Entry level Sales 7.1 (International)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-7-1/"
    },
    {
        "name": "Entry Level Sales Sift Out 7.1",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-sift-out-7-1/"
    },
    {
        "name": "Entry Level Sales Solution",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-solution/"
    },
    {
        "name": "Sales Representative Solution",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/sales-representative-solution/"
    },
    {
        "name": "Sales Support Specialist Solution",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/sales-support-specialist-solution/"
    },
    {
        "name": "Technical Sales Associate Solution",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/technical-sales-associate-solution/"
    },
    {
        "name": "SVAR - Spoken English (Indian Accent)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/svar-spoken-english-indian-accentnew/"
    },
    {
        "name": "Sales & Service Phone Solution",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/sales-and-service-phone-solution/"
    },
    {
        "name": "Sales & Service Phone Simulation",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/sales-and-service-phone-simulation/"
    },
    {
        "name": "English Comprehension (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/english-comprehension-new/"
    }
]

output = []

# Headers to simulate a real browser
headers = {
    "User-Agent": "Mozilla/5.0"
}

for product in products:
    try:
        response = requests.get(product["url"], headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        print("ge")
        # Updated logic: Find <h4>Description</h4> and then next <p>
        desc_header = soup.find("h4", string="Description")
        if desc_header:
            desc_para = desc_header.find_next("p")
            if desc_para:
                description = desc_para.get_text(strip=True)
            else:
                description = "Description paragraph not found"
        else:
            description = "Description header not found"

        output.append({
            "name": product["name"],
            "url": product["url"],
            "description": description
        })

        print(f"Scraped: {product['name']}")
        time.sleep(1)  # Delay for server courtesy

    except Exception as e:
        print(f"Error scraping {product['url']}: {e}")
        output.append({
            "name": product["name"],
            "url": product["url"],
            "description": "Error retrieving description"
        })


# Save to JSON
with open("shl_product_descriptions.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("Descriptions saved to 'shl_product_descriptions.json'")
