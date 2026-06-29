import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

class IndeedScraper:
    """Scrape jobs from Indeed India"""
    
    BASE_URL = "https://in.indeed.com"
    
    @staticmethod
    def scrape_jobs(keyword: str, location: str = "India", pages: int = 1):
        """Scrape jobs from Indeed"""
        jobs = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            for page in range(pages):
                start = page * 10
                url = f"{IndeedScraper.BASE_URL}/jobs?q={keyword}&l={location}&start={start}"
                
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                for card in job_cards:
                    try:
                        title = card.find('h2', class_='jobTitle')
                        company = card.find('span', class_='companyName')
                        location_tag = card.find('div', class_='companyLocation')
                        salary = card.find('span', class_='salary-snippet')
                        snippet = card.find('div', class_='job-snippet')
                        job_link = card.find('a', class_='jcs-JobTitle')
                        
                        if title and company:
                            job_obj = {
                                'title': title.text.strip(),
                                'company': company.text.strip(),
                                'location': location_tag.text.strip() if location_tag else location,
                                'salary': salary.text.strip() if salary else 'Not specified',
                                'description': snippet.text.strip() if snippet else '',
                                'skills': IndeedScraper.extract_skills(snippet.text if snippet else ''),
                                'source': 'Indeed',
                                'sourceUrl': IndeedScraper.BASE_URL + job_link['href'] if job_link else '',
                                'postedDate': datetime.now()
                            }
                            jobs.append(job_obj)
                    except Exception as e:
                        print(f"Error parsing job card: {e}")
                        continue
        
        except Exception as e:
            print(f"Error scraping Indeed: {e}")
        
        return jobs
    
    @staticmethod
    def extract_skills(text):
        """Extract technical skills from job description"""
        skills_list = [
            'python', 'java', 'javascript', 'sql', 'aws', 'docker',
            'react', 'angular', 'node.js', 'fastapi', 'django',
            'kubernetes', 'mongodb', 'postgresql', 'rest api',
            'machine learning', 'tensorflow', 'pandas', 'git'
        ]
        
        text_lower = text.lower()
        found_skills = [skill for skill in skills_list if skill in text_lower]
        return found_skills