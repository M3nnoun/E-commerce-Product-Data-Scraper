import csv
import requests
from bs4 import BeautifulSoup
from lxml import html
import time

def print_list(items):
    for i, item in enumerate(items, start=1):
        print(f"{i}. {item}")

def extract_links_from_html(html_content):
   # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the <ul> element by id and class
    ul_element = soup.find('ul', {'id': 'mobile-navigation', 'class': 'header-nav nasa-menu-accordion nasa-menu-for-mobile'})

    # Initialize a list to store the extracted data as dictionaries
    li_data_list = []

    # Extract text and link (href) from each <li> element within the <ul> element
    if ul_element:
        li_elements = ul_element.find_all('li')
        for li in li_elements:
            anchor = li.find('a')
            if anchor:
                li_text = anchor.text.strip()
                if li_text:
                    li_link = anchor.get('href')
                    li_data = [li_text, li_link]  # Create a dictionary with text as key and href as value
                    li_data_list.append(li_data)
    
    return li_data_list

def get_all_products_from_page(url):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content using lxml
            tree = html.fromstring(response.text)

            # Use the provided XPath expression to find all matching elements
            a_elements = tree.xpath("//a[@class='name woocommerce-loop-product__title nasa-show-one-line']")

            # Extract the href attribute from each <a> element
            links = [a.get('href') for a in a_elements if a.get('href')]

            return links

        else:
            print(f"Failed to fetch the page. Status code: {response.status_code}")
            return []

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

def get_product_info(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            result = {}

            h1_element = soup.find('h1', class_="product_title")
            if h1_element:
                h1_text = h1_element.text.strip()
                result['product_title'] = h1_text

            p_element = soup.find('p', class_="price nasa-single-product-price")
            if p_element:
                del_tag = p_element.find('del')
                ins_tag = p_element.find('ins')

                bdi_text_in_del = del_tag.find('bdi').text.strip().replace("\xa0$", "")
                bdi_text_in_ins = ins_tag.find('bdi').text.strip().replace("\xa0$", "")
                result['old_price'] = bdi_text_in_del
                result['product_price'] = bdi_text_in_ins

            span_elements = soup.select('div.nasa-attr-ux_wrap span.nasa-attr-text')
            text_list = [span.text.upper() for span in span_elements]
            if text_list:
                result['sizes_values'] = text_list
                # print("hello from if")
            else:
                option_elements = soup.select('select#pa_taglia option')
                option_values = [option['value'].upper() for option in option_elements if option['value']]
                result['sizes_values'] = option_values              

            option_elements = soup.select('select#pa_colore option')
            option_values = [option['value'].upper() for option in option_elements if option['value']]
            result['color_options'] = option_values

            return result
        else:
            print(f"Failed to fetch the page. Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def add_product_to_dict(product_dict, category, product_link):
    if category not in product_dict:
        product_dict[category] = {}
    product_dict[category][product_link] = get_product_info(product_link)

def save_dict_to_csv(product_dict, csv_filename):
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['category', 'product_link', 'title', 'old_price','product_price', 'sizes_values', 'color_options']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write the header row to the CSV file
        writer.writeheader()
        
        # Iterate through the dictionary and write each product as a row
        for category, products in product_dict.items():
            for product_link, product_data in products.items():
                writer.writerow({
                    'category': category,
                    'product_link': product_link,
                    'title': product_data['product_title'],
                    'old_price': product_data['old_price'],
                    'product_price': product_data['product_price'],
                    'sizes_values': ', '.join(product_data['sizes_values']),  # Convert sizes list to a comma-separated string
                    'color_options': product_data['color_options']
                })

HTML_NAV_BAR = """
<ul id="mobile-navigation" class="header-nav nasa-menu-accordion nasa-menu-for-mobile" data-show="1">

<li class="menu-item menu-item-type-custom menu-item-object-custom menu-item-has-children menu-parent-item default-menu root-item nasa_even li_accordion"><a href="javascript:void(0);" class="accordion"></a><a href="#" class="nasa-title-menu"><i class="pe-7s-angle-down nasa-open-child"></i>Accessories<i class="fa fa-angle-right nasa-has-items-child"></i></a><div class="nav-dropdown-mobile" style="display: none;"><ul class="sub-menu"><li class="menu-item menu-item-type-post_type menu-item-object-page"><a title="BELT" href="https://luxury-drip.com/belt/" class="nasa-title-menu">BELT</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page default-menu root-item nasa_odd"><a title="Jacket" href="https://luxury-drip.com/j/" class="nasa-title-menu"><i class="pe-7s-angle-down nasa-open-child"></i>Jacket</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page default-menu root-item nasa_even"><a title="Planet" href="https://luxury-drip.com/planert/" class="nasa-title-menu"><i class="pe-7s-angle-down nasa-open-child"></i>Planet</a></li>

</ul>

"""
category_names_links = extract_links_from_html(HTML_NAV_BAR)
products_dict = {}
# for link in links:
#     add_product_to_dict(product_dict,item,link)

# print(get_product_info(url))

for item in category_names_links:
    category_name=item[0]
    category_link=item[1]
    products_links=get_all_products_from_page(category_link)
    time.sleep(10)
    for product_link in products_links:
        add_product_to_dict(products_dict,category_link,product_link)
    print(f"{category_name} is done ....")

save_dict_to_csv(products_dict, './products.csv')

