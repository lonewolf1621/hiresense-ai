import requests
from bs4 import BeautifulSoup
from datetime import datetime

class NaukriScraper:
    """Scrape jobs from Naukri.com"""
    
    BASE_URL = "https://www.naukri.com"
    
    @staticmethod
    def scrape_jobs(keyword: str, location: str = "", pages: int = 1):
        """Scrape jobs from Naukri"""
        jobs = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            for page in range(1, pages + 1):
                url = f"{NaukriScraper.BASE_URL}/jobs-{keyword}-{location}-{page}"
                
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_cards = soup.find_all('article', class_='jobTuple')
                
                for card in job_cards:
                    try:
                        title = card.find('a', class_='jobTitle')
                        company = card.find('a', class_='companyName')
                        location_tag = card.find('span', class_='loc')
                        salary = card.find('span', class_='salaryText')
                        snippet = card.find('span', class_='job-snippet')
                        
                        if title and company:
                            job_obj = {
                                'title': title.text.strip(),
                                'company': company.text.strip(),
                                'location': location_tag.text.strip() if location_tag else location,
                                'salary': salary.text.strip() if salary else 'Not specified',
                                'description': snippet.text.strip() if snippet else '',
                                'skills': NaukriScraper.extract_skills(snippet.text if snippet else ''),
                                'source': 'Naukri',
                                'sourceUrl': title.get('href', ''),
                                'postedDate': datetime.now()
                            }
                            jobs.append(job_obj)
                    except Exception as e:
                        print(f"Error parsing job: {e}")
                        continue
        
        except Exception as e:
            print(f"Error scraping Naukri: {e}")
        
        return jobs
    
    @staticmethod
    def extract_skills(text):
        """Extract technical skills"""
        skills_list = [
            'python', 'java', 'javascript', 'sql', 'aws', 'docker',
            'react', 'angular', 'node.js', 'fastapi', 'django',
            'kubernetes', 'mongodb', 'postgresql', 'rest api',
            'machine learning', 'tensorflow', 'pandas', 'git',
            'c++', 'c#', '.net', 'php', 'golang', 'scala'
        ]
        
        text_lower = text.lower()
        found_skills = [skill for skill in skills_list if skill in text_lower]
        return found_skills