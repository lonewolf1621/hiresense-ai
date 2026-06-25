import json
import os


def load_companies():
    """Load company database"""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "companies.json")
    
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading companies: {e}")
        return {"industries": {}}


def get_industries():
    """Get list of all industries"""
    companies = load_companies()
    industries = []
    
    for key, value in companies.get("industries", {}).items():
        industries.append({
            "key": key,
            "name": value.get("industry_name", key),
            "description": value.get("description", "")
        })
    
    return industries


def get_companies_by_industry(industry_key):
    """Get all companies in an industry"""
    companies = load_companies()
    industry = companies.get("industries", {}).get(industry_key, {})
    
    return {
        "industry": industry.get("industry_name", industry_key),
        "description": industry.get("description", ""),
        "companies": industry.get("companies", [])
    }


def get_company_details(industry_key, company_name):
    """Get detailed info about a company"""
    companies_data = load_companies()
    industry = companies_data.get("industries", {}).get(industry_key, {})
    
    for company in industry.get("companies", []):
        if company.get("name").lower() == company_name.lower():
            return company
    
    return None


def get_company_insights(industry_key):
    """Get insights for an industry"""
    data = get_companies_by_industry(industry_key)
    
    if not data.get("companies"):
        return {}
    
    companies = data["companies"]
    
    # Calculate average salary
    salaries = [c.get("salary_range", "0-0") for c in companies]
    
    # Extract salary numbers
    try:
        salary_nums = []
        for s in salaries:
            nums = ''.join(filter(str.isdigit, s.split('-')[0]))
            if nums:
                salary_nums.append(int(nums))
        avg_salary = sum(salary_nums) / len(salary_nums) if salary_nums else 0
    except:
        avg_salary = 0
    
    return {
        "total_companies": len(companies),
        "company_names": [c.get("name") for c in companies],
        "average_salary": f"₹{int(avg_salary)}-{int(avg_salary) + 10}+ LPA",
        "common_tech_stack": list(set([tech for c in companies for tech in c.get("tech_stack", [])]))[:10],
        "hiring_roles": list(set([role for c in companies for role in c.get("hiring_roles", [])]))
    }