import time
from selenium import webdriver
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import os


class GuidelineScraper():
    def __init__(self, url, folder_path):
        self.base_url = 'https://register.awmf.org'
        self.folder_path = folder_path

    def get_fachgesellschaften_links(self):
        overview_url = 'https://register.awmf.org/de/leitlinien/aktuelle-leitlinien'
        driver = webdriver.Chrome()  # Ensure you have ChromeDriver installed
        driver.get(overview_url)

        # Waiting for the page to load completely
        time.sleep(15)

        # Extract the page source or interact with the loaded content
        guideline_overview_page = driver.page_source

        # Close the browser
        driver.quit()
        soup = BeautifulSoup(guideline_overview_page, 'html.parser')
        fachgesellschaften_links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and '/de/leitlinien/aktuelle-leitlinien/fachgesellschaft/' in href:
                fachgesellschaften_links.append(href)

        fachgesellschaften_links = list(set(fachgesellschaften_links))  # Remove duplicates
        print(f"Found {len(fachgesellschaften_links)} unique links to Fachgesellschaften.")
        return fachgesellschaften_links
    
    def get_guideline_links(self, fachgesellschaften_links):
        guideline_links = []
        failed_links = []
        for link in fachgesellschaften_links:
            base_url = 'https://register.awmf.org'
            driver = webdriver.Chrome()  # Ensure you have ChromeDriver installed
            driver.get(base_url + link)

            # Waiting for the page to load completely
            time.sleep(10)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            ion_rows = soup.find_all('ion-row', class_='guideline-listing-row')
            
            # Iterate over each <ion-row> and extract the href attributes of <a> tags
            for row in ion_rows:
                links = row.find_all('a')  # Find all <a> tags in the current <ion-row>
                hrefs = [link['href'] for link in links if 'href' in link.attrs]  # Extract href attributes
                guideline_links.extend(hrefs)  # Add the hrefs to the list
            

            # check if the page has loaded correctly
            if len(hrefs) == 0:
                failed_links.append(fachgesellschaft_links[i])
                print(f"FAILED to load page: {fachgesellschaft_links[i]}")
            else:
                print(f"Loaded page successfully: {link}")

            # Close the browser
            driver.quit()
            
        guideline_links = list(set(guideline_links))  
        # read the pdf_links from the file
        with open('guideline_links.txt', 'r') as f:
            guideline_links = f.readlines()
        return guideline_links
    
    def process_guideline_page(soup, guideline_number):
        meta = {
            'title': soup.find('h1').text,
            'Registiernummer': soup.find_all('h3')[1].text,
        }

        keywords = [
            'Version:',
            'Stand:',
            'Gültig bis:',
            'Patienteninformation:',
            'Verbindung zu themenverwandten Leitlinien:',
            'Federführende Fachgesellschaft(en):',
            'Adressaten:',
            'Patientenzielgruppe:',
            'Versorgungsbereich:',
            'Beteiligung weiterer AWMF-Fachgesellschaften:',
            'Gründe für die Themenwahl:',
            'Zielorientierung der Leitlinie:',
            'Schlüsselwörter:',
        ]

        # Iterate over all <ion-row> elements and extract metadata
        for row in soup.find_all('ion-row'):
            for keyword in keywords:
                if keyword in row.text:
                    meta[keyword[:-1]] = row.find_all('ion-col')[1].text
                    break
        
        pdf_links = []
        links = soup.find_all('a')  # Find all <a> tags in the current <ion-row>
        for l in links:
            href = l.get('href')
            if href and '/assets/guidelines/' in href:
                pdf_links.append(href)
        
        meta['pdf_links'] = pdf_links
        return meta
    
    def get_guideline_metadata(self, guideline_links):
        

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode

        failed_links = []
        metadata = {}
        for link in tqdm(guideline_links, desc="Retrieving metadata"):
            driver = webdriver.Chrome(options=chrome_options)  # Ensure you have ChromeDriver installed
            driver.get(link)

            # Wait for a specific amount of time (e.g., 10 seconds)
            time.sleep(7)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            guideline_number = link.split('/')[-1]
            try:
                metadata[guideline_number] = process_guideline_page(soup, guideline_number)
            except Exception as e:
                failed_links.append(link)

            # Close the browser
            driver.quit()
            

        # save metadata to a file
        with open('metadata.json', 'w') as f:
            json.dump(metadata, f)
        
    def load_metadata_df(self):
        metadata_df = pd.read_json('metadata.json').T
        return metadata_df
    
    def download_file(url, folder_path, idd):
        # Get the filename from the URL
        filename = os.path.basename(idd + '.pdf')
        file_path = os.path.join(folder_path, filename)
        
        base_url = 'https://register.awmf.org'
        # Send a GET request to the URL
        response = requests.get(base_url + url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Write the content to a file
            with open(file_path, 'wb') as file:
                file.write(response.content)
        else:
            print(f"Failed to download: {url} (Status code: {response.status_code})")
    
    def download_files(self, metadata):
        
        for key, row in tqdm(metadata_df.iterrows()):
            if 'pdf_links' in row and len(row['pdf_links']) > 0:
                pdf_link = row['pdf_links'][0]
                # check if pdf already exists
                if os.path.exists(os.path.join(self.folder_path, row.name + '.pdf')):
                    continue
                download_file(pdf_link, self.folder_path, row.name)
            else:
                print(f"No PDF link found for {row['Registiernummer']}")
            time.sleep(2)
    
    def scrape(self):
        # Create the folder if it doesn't exist
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        # Get the links to the Fachgesellschaften
        fachgesellschaften_links = get_fachgesellschaften_links()

        # Get the links to the guidelines
        guideline_links = get_guideline_links(fachgesellschaften_links)

        # Get the metadata for each guideline
        metadata = get_guideline_metadata(guideline_links)

        # Load the metadata into a DataFrame
        metadata_df = load_metadata_df()

        # Download the PDF files
        download_files(metadata_df)
            

class Guideline():
    def __init__(self, metadata, pdf_file_path):
        self.metadata = metadata
        self.guideline_number = metadata['Registiernummer']
        self.version = metadata['version']
        self.valid_until = metadata['Gültig bis']
        self.related_topics = metadata['Verbindung zu themenverwandten Leitlinien']
        self.patient_information = metadata['Patienteninformation']
        self.keywords = metadata['Schlüsselwörter']
        self.area_of_application = metadata['Versorgungsbereich']
        self.target_group = metadata['Patientenzielgruppe']
        self.main_society = metadata['Federführende Fachgesellschaft(en)']
        self.associated_societies = metadata['Beteiligung weiterer AWMF-Fachgesellschaften']
        self.adressaten = metadata['Adressaten']
        self.reason_for_topic_choice = metadata['Gründe für die Themenwahl']
        self.objectives = metadata['Zielorientierung der Leitlinie']
        self.pdf_links = metadata['pdf_links']
        self.keywords = metadata.keys()
    

if __name__ == "__main__":
    # Example usage
    scraper = GuidelineScraper(url='https://register.awmf.org', folder_path='guidelines')
    scraper.scrape()
    print("Scraping completed successfully.")