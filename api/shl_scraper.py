import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.shl.com/products/product-catalog/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SHL_FILTER_IDS = {
    "job_family": {
        "Business": 1,
        "Clerical": 2,
        "Contact Center": 3,
        "Customer Service": 4,
        "Information Technology": 5,
        "Safety": 6,
        "Sales": 7,    
    },
    "job_level": {
        "Graduate": 6,
        "Entry-Level": 2,
        "Executive": 3,
        "Director": 1,
        "Front Line Manager": 4,
        "Manager": 7,
        "Mid-Professional": 8,
        "Professional Individual Contributor": 9,
        "Supervisor": 10,
        "General Population": 5,
    },
    "industry": {
        "Banking/Finance": 1,
        "Healthcare": 2,
        "Hospitality": 3,
        "Insurance": 4,
        "Manufacturing": 5,
        "Oil & Gas": 6,
        "Retail": 7,
        "Telecommunications": 8,
    },
    "language": {
        "Arabic" : 1,
        "Bulgarian" : 2,
        "Chinese Simplified" : 3,
        "Chinese Traditional" : 4,
        "Croatian" : 5,
        "Czech" : 6,
        "Danish" : 7,
        "Dutch" : 8,
        "English (Australia)" : 9,
        "English (Canada)" : 10,    
        "English International" : 11,        
        "English (Malaysia)" : 12 ,
        "English (Singapore)" : 13 , 
        "English (South Africa)" : 14,
        "English (USA)" : 15,
        "Estonian" : 16 ,
        "Finnish": 17,
        "Flemish": 18,
        "French" : 19 , 
        "French (Belgium)" : 20 , 
        "French (Canada)" : 21 ,
        "German" : 22 ,
        "Greek" : 23 ,
        "Hungarian" : 24 ,
        "Icelandic" : 25 ,
        "Indonesian" : 26 ,
        "Italian" : 27 ,
        "Japanese" : 28 ,
        "Korean" : 29 ,
        "Latin American Spanish" : 30 ,
        "Latvian" : 31 ,
        "Lithuanian" : 32 ,
        "Malay" : 33 ,
        "Norwegian" : 34 ,
        "Polish" : 35 ,
        "Portuguese" : 36 ,
        "Portuguese (Brazil)" : 37 ,
        "Romanian" : 38 ,
        "Russian" : 39 ,
        "Serbian" : 40 ,
        "Slovak" : 41 ,
        "Spanish" : 42 ,
        "Swedish" : 43 ,
        "Thai" : 44 ,
        "Turkish" : 45 ,
        "Vietnamese" : 46 ,
    }
}

def build_search_url(filters):
    urls = []
    
    if "keywords" in filters and filters["keywords"]:
        keywords = [k.strip() for k in filters["keywords"].split(",")]
        for keyword in keywords:
            keyword_filters = filters.copy()
            keyword_filters["keyword"] = keyword
            url = build_single_search_url(keyword_filters)
            with open("all_urls.txt", "a") as f:
                f.write("\n"+url)                    
            urls.append(url)
    else:
        urls.append(build_single_search_url(filters))
    return urls

def build_single_search_url(filters):
    params = []
    if "keyword" in filters and filters["keyword"]:
        keyword = filters["keyword"].replace(" ", "+")
        params.append(f"keyword={keyword}")
        params.append("action_doFilteringForm=Search")
    
    for key in ["job_family", "job_level", "industry", "language"]:
        if key in filters and filters[key]:
            value = filters[key]
            id_map = SHL_FILTER_IDS.get(key, {})
            if value in id_map:
                params.append(f"{key}={id_map[value]}")
    
    params.append("f=1")
    
    query_string = "&".join(params)
    return f"{BASE_URL}?{query_string}"

def parse_duration(duration_text):
    """Parse duration text to extract minutes."""
    if not duration_text:
        return 0
        
    if "-" in duration_text:
        parts = duration_text.split("-")
        if len(parts) == 2:
            try:
                min_duration = int(''.join(filter(str.isdigit, parts[0])))
                max_duration = int(''.join(filter(str.isdigit, parts[1])))
                return (min_duration + max_duration) // 2  
            except (ValueError, TypeError):
                pass
    
    try:
        return int(''.join(filter(str.isdigit, duration_text)))
    except (ValueError, TypeError):
        return 0

def fetch_assessments(filters, max_retries=3, retry_delay=2):
    urls = build_search_url(filters)  #
    all_assessments = []

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for url in urls:
        logger.info(f"Fetching SHL assessments from URL: {url}")
        assessments_from_url = []

        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table_responsive_list = soup.find_all('div', class_='custom__table-responsive')
                
                for table_responsive in table_responsive_list:
                    table = table_responsive.find('table')
                    if not table:
                        logger.warning("Could not find table inside a responsive div.")
                        continue

                    for row in table.find_all('tr')[1:]:  
                        try:
                            cells = row.find_all('td')
                            if len(cells) < 4:
                                continue

                            title_cell = cells[0]
                            link = title_cell.find('a')
                            if not link or not link.has_attr('href'):
                                continue

                            relative_url = link['href']
                            full_url = urljoin(BASE_URL, relative_url)

                        
                            assessment = {
                                'url': full_url,
                            }

                            assessments_from_url.append(assessment)

                        except Exception as e:
                            logger.error(f"Error processing row: {str(e)}")
                            continue
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to fetch SHL page after {max_retries} attempts: {url}")
        
        all_assessments.extend(assessments_from_url)
    return all_assessments


def get_assessment_details(assessment_url):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(assessment_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        details = {'url': assessment_url}

        rows = soup.select('.product-catalogue-training-calendar__row')

        for row in rows:
            heading = row.find('h4')
            content = row.find('p')
            if not heading or not content:
                continue

            title = heading.get_text(strip=True).lower()
            value = content.get_text(strip=True)

            if 'description' in title:
                details['description'] = value
            elif 'job level' in title:
                details['job_levels'] = [lvl.strip() for lvl in value.split(',') if lvl.strip()]
            elif 'language' in title:
                details['languages'] = [lang.strip() for lang in value.split(',') if lang.strip()]
            elif 'assessment length' in title:
                details['assessment_time'] = value

        test_type_span = soup.select_one('.product-catalogue__key')
        if test_type_span:
            details['test_type'] = test_type_span.get_text(strip=True)

        remote_text_container = soup.find('p', string=lambda t: t and "Remote Testing" in t)
        if remote_text_container and remote_text_container.find('span', class_='catalogue__circle -yes'):
            details['remote_testing'] = 'Yes'
        else:
            details['remote_testing'] = 'No'

        return details

    except Exception as e:
        logger.error(f"Error fetching assessment details: {str(e)}")
        return {}

def save_assessments(assessment_urls, output_file='assessments_data.json'):
    all_data = []

    for url_dict in assessment_urls:
        data = get_assessment_details(url_dict['url'])
        if data:
            all_data.append(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(all_data)} assessments to {output_file}")