from utils.clean_data import clean_company_name,clean_roles

roles=input("Enter role :")
company_name=input("Enter company_name :")

roles=clean_roles(roles)
print(roles)

company_name=clean_company_name(company_name)
print(company_name) 