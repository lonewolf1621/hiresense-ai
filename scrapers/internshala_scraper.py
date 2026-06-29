import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

class InternshalaScraper:
    """Scrape internships/jobs from Internshala"""
    
    BASE_URL = "https://internshala.com"
    
    @staticmethod
    def scrape_jobs(keyword: str, location: str = "", pages: int = 1):
        """Scrape jobs from Internshala"""
        jobs = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            # Internshala uses JavaScript, so we'll use a simpler approach
            for page in range(pages):
                url = f"{InternshalaScraper.BASE_URL}/jobs/{keyword}-jobs-in-{location}/?page={page+1}"
                
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_cards = soup.find_all('div', class_='internship_card')
                
                for card in job_cards:
                    try:
                        title = card.find('h3', class_='job-title')
                        company = card.find('p', class_='company-name')
                        location_tag = card.find('p', class_='location')
                        stipend = card.find('p', class_='stipend')
                        
                        if title and company:
                            job_obj = {
                                'title': title.text.strip(),
                                'company': company.text.strip(),
                                'location': location_tag.text.strip() if location_tag else location,
                                'salary': stipend.text.strip() if stipend else 'Not specified',
                                'description': card.text.strip(),
                                'skills': InternshalaScraper.extract_skills(card.text),
                                'source': 'Internshala',
                                'sourceUrl': card.find('a').get('href', '') if card.find('a') else '',
                                'postedDate': datetime.now()
                            }
                            jobs.append(job_obj)
                    except Exception as e:
                        print(f"Error parsing job: {e}")
                        continue
        
        except Exception as e:
            print(f"Error scraping Internshala: {e}")
        
        return jobs
    
    @staticmethod
    def extract_skills(text):
        """Extract technical skills"""
        skills_list = [
            'python', 'java', 'javascript', 'sql', 'aws', 'docker',
            'react', 'angular', 'node.js', 'fastapi', 'django',
            'kubernetes', 'mongodb', 'postgresql', 'rest api',
            'machine learning', 'tensorflow', 'pandas', 'git',
            'php', 'wordpress', 'figma', 'ui/ux', 'graphic design'
        ]
        
        text_lower = text.lower()
        found_skills = [skill for skill in skills_list if skill in text_lower]
        return found_skills