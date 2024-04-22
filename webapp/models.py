import logging, json
from openai import OpenAI
import pandas as pd
from django.utils.text import slugify
from .openPDF import DataFactory

LOGGER = logging.getLogger(__name__)

class InsuranceDeposit:

	def get_data(self):
		system_msg = 'You are an statement processing solution.'
		query = '''
		extract data from above statement and return only the json containing the following -
		each line item present in the statement with
		patient_first_name, patient_last_name, reference_number,
		service_date as dd/mm/YYYY, submitted_expense, eligible_expense, amount_paid -
		#for each line item present in the statement.
		json=
		'''
		user_msg = file_text + '\n\n' + query
		response = self.client.chat.completions.create(
			model="gpt-3.5-turbo",
			messages=[{"role": "system", "content": system_msg},
			{"role": "user", "content": user_msg}]
		)

		data = json.loads(response.choices[0].message.content)
		for row in data['line_items']:
			LOGGER.error(row)
			fn = row['patient_first_name']
			ln = row['patient_last_name']
			sd = row['service_date']
			se = float(row['submitted_expense'])
			row['key'] = slugify("{} {} {} {:.2f}".format(fn, ln, sd, se))
		return data['line_items']

	def get_invoice_data(self, file_text):
		system_msg = 'You are an invoice processing solution.'
		query = '''
		extract data from above invoice and return only the json containing the following -
		payer_name (left top corner) and for each line item excluding "Write Off" -
		service_date as dd/mm/YYYY, total
		#for each line item present in the invoice.
		json=
		'''
		user_msg = file_text + '\n\n' + query

		response = self.client.chat.completions.create(
			model="gpt-3.5-turbo",
			messages=[{"role": "system", "content": system_msg},
			{"role": "user", "content": user_msg}]
		)
		data = json.loads(response.choices[0].message.content)
		for row in data['line_items']:
			name = data['payer_name']
			sd = row['service_date']
			se = float(row['total'])
			row['key'] = slugify("{} {} {}:.2".format(name, sd, se))
		return data


class CoverageProviderStatementReader:

	def read(self):
		files = DataFactory().list_source_dir()
		data = []
		content = ''
		for f in files:
			content += DataFactory().read_pdf(f)
			content += '\n\n'
		return OpenAIDriver().get_statement_data(content)

