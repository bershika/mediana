## TESTBED
import os
import django
from django.conf import settings
import pdf2image
from PIL import Image
import pytesseract

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")

django.setup()


# Get the list of all files and directories
#settings.configure()
path = os.path.join(settings.BASE_DIR, 'data')
dir_list = os.listdir(path)
# prints all files
for file_name in dir_list:
    print("Files and directories in '", file_name, "' :")



# image = pdf2image.convert_from_path('invoice.pdf')
# for pagenumber, page in enumerate(image):
#     detected_text = pytesseract.image_to_string(page)

# system_msg = 'You are an invoice processing solution.'

# query = '''what is this document?'''

# '''
# extract data from above invoice and return only the json containing the following -
# invoice_date, invoice_number, seller_name, seller_address, total_amount, and each line item present in the invoice.
# json=
# '''

# user_msg = detected_text + '\n\n' + query

# response = client.chat.completions.create(model="gpt-3.5-turbo",
#                                         messages=[{"role": "system", "content": system_msg},
#                                          {"role": "user", "content": user_msg}])

# print(response.choices[0].message.content)
