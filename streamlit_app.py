import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Function to scrape Trustpilot
def scrape_trustpilot_details(start_url, max_pages):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0 Safari/537.36"
    }

    all_links = []
    current_page = 1

    # Step 1: Collect all review links from search results
    while current_page <= max_pages:
        st.write(f"Scraping links from page {current_page}...")
        response = requests.get(start_url, headers=headers)
        if response.status_code != 200:
            st.write(f"Failed to fetch page {current_page}. Status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract review links
        review_links = [
            "https://www.trustpilot.com" + link["href"]
            for link in soup.find_all("a", href=True)
            if "/review/" in link["href"]
        ]
        all_links.extend(review_links)

        # Find the "Next" button or next page link
        next_button = soup.find("a", {"aria-label": "Next page"})
        if next_button and "href" in next_button.attrs:
            start_url = "https://www.trustpilot.com" + next_button["href"]
            current_page += 1
            time.sleep(1)  # Pause to avoid rate-limiting
        else:
            st.write("No more pages to scrape.")
            break

    # Deduplicate links
    all_links = list(set(all_links))
    st.write(f"Collected {len(all_links)} links.")

    # Step 2: Visit each link and extract required details
    business_data = []
    for index, link in enumerate(all_links, start=1):
        st.write(f"Scraping details from link {index}/{len(all_links)}: {link}")
        try:
            response = requests.get(link, headers=headers)
            if response.status_code != 200:
                st.write(f"Failed to fetch details from {link}. Status code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract details with safe fallback
            business_name = soup.find("h1").text.strip().split('\xa0')[0] if soup.find("h1") else "N/A"
            website_link = (
                soup.find("a", {"href": True, "rel": "noopener"})["href"].split('?')[0]
                if soup.find("a", {"href": True, "rel": "noopener"})
                else "N/A"
            )
            contact_number = (
                soup.find("a", href=lambda href: href and href.startswith("tel:")).text.strip()
                if soup.find("a", href=lambda href: href and href.startswith("tel:"))
                else "N/A"
            )
            email = (
                soup.find("a", href=lambda href: href and href.startswith("mailto:")).text.strip()
                if soup.find("a", href=lambda href: href and href.startswith("mailto:"))
                else "N/A"
            )

            # Append to the list
            business_data.append({
                "Business Name": business_name,
                "Website Link": website_link,
                "Contact Number": contact_number,
                "Email": email
            })
        except Exception as e:
            st.write(f"Error scraping link {link}: {e}")

        # Pause to avoid rate-limiting
        time.sleep(2)

    # Step 3: Compile DataFrame
    df = pd.DataFrame(business_data)
    return df

# Streamlit app
st.title("Trustpilot Scraper")

# Input bar for Trustpilot URL
start_url = st.text_input("Enter the Trustpilot category or search URL:", "https://www.trustpilot.com/categories/salons_clinics")

# Number selector for maximum pages to scrape
max_pages = st.number_input("Number of pages to scrape:", min_value=1, max_value=20, value=1, step=1)

# Button to start scraping
if st.button("Start Scraping"):
    st.write("Scraping started...")
    df = scrape_trustpilot_details(start_url, max_pages)

    # Display DataFrame
    st.write("Scraping completed. Here's a preview of the data:")
    st.dataframe(df)

    # Provide download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="trustpilot_business_data.csv",
        mime="text/csv"
    )
