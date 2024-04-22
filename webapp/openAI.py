import logging, json
import os, re, io
from openai import OpenAI
import pandas as pd
from django.utils.text import slugify
from django.conf import settings

from .openPDF import DataFactory

LOGGER = logging.getLogger(__name__)
API_KEY = os.environ.get('AI_KEY')

SUNLIFE 	= "Sun Life" # claim num
CANLIFE 	= "Canada Life"
BLUECROSS 	= "Blue Cross"
DESJARDINS 	= "Desjardins"
EMPIRELIFE 	= "Empire Life"
GREENSHIELD = "Green Shield"
CHAMBERS	= "Chambers"
XCHANGE		= "ClaimsXChange" # The NXG Group, NexgenR, Global Benefits, The Co-operators
COOP  		= "The Co-operators"
EQLIFE 		= "Equitable Life of Canada"
GROUPHEALTH = "GroupHEALTH"
GROUPSOURCE = "GroupSource"
MANULIFE 	= "Manulife"
MAXBENEFIT 	= "Maximum Benefit"
TELUS  		= "TELUS AdjudiCare"

PROVIDERS = [
	SUNLIFE,
	CANLIFE,
	BLUECROSS,
	DESJARDINS,
	EMPIRELIFE,
	GREENSHIELD,
	CHAMBERS,
	XCHANGE,
	COOP,
	EQLIFE,
	GROUPHEALTH,
	GROUPSOURCE,
	MANULIFE,
	MAXBENEFIT,
	TELUS,
]

STATEMENT_TYPE 	= 'statement'
CLAIM_TYPE 		= 'claim'
UNKNOWN 		= 'unknown'


class DriverFactory:

	def get_driver(self):
		return OpenAIDriver()

class OpenAIDriver:
	client = OpenAI(api_key=API_KEY)

	@staticmethod
	def _name_variations(name):
		return [name, name.casefold(), name.replace(' ', ''), slugify(name)]

	@staticmethod
	def _text_contains(keyword_list, file_text, provider=None):
		try:
			file_text = re.sub(r'\s+', ' ', file_text.casefold()) #remove multiple spaces
			### improve
			file_text = re.sub(r"\s(\S)\s", '\\1', file_text)  #condense space-separated letters
		except Exception as e: LOGGER.error("Error in _text_contains {}".format(e))
		# if provider == MANULIFE:
			# LOGGER.error('1*******')
			# LOGGER.error(file_text)
			# LOGGER.error('2*******')
			# LOGGER.error(re.sub(r"\s(\S)\s",'\\1', file_text))

		for k in keyword_list:
			sanitized_name = k.casefold()
			LOGGER.error(sanitized_name)
			if sanitized_name in file_text: return True
			# if sanitized_name in re.sub(r"\s(\S)\s",'\\1', file_text): return True

	def get_insurance_provider(self, file_text):
		try: file_text = file_text.casefold()
		except Exception as e: LOGGER.error(e)
		for p in PROVIDERS:
			keyword_list = self._name_variations(p)
			if self._text_contains(keyword_list, file_text, p): return p

	def get_doctype(self, file_text):
		statement_keywords = [
			'Direct Deposit Statement',
			'NOT NEGOTIABLE',
			'payment has been issued',
			'Notice of Payment',
			'Your payment for claim',
			'Your claim has been paid'
			'Payment ID',
			'EFT No',
			'processed the payment',
			'payments deposited into your account',
		]

		claim_keywords = [
			'Explanation of Benefits',
			'Your claim has been processed',
			'Claim Submission Results',
			'THIS CLAIM HAS BEEN SUBMITTED',
			'Submit a Claim',
			'Expected Payment Date'
		]
		# todo: green shield statement == claim except for EFT -
		# to diff from random doc, check for Claim word and a table
		if self._text_contains(statement_keywords, file_text): return STATEMENT_TYPE
		if self._text_contains(claim_keywords, file_text): return CLAIM_TYPE
		if CLAIM_TYPE in file_text: return CLAIM_TYPE

	def get_statement_prompt(self, provider):
		system_msg = '''
		You are an insurance statement processing solution.
		Find statement details and line items and provide your answer in JSON as followig:
		'''
		# "payment_number": { "type": "string" },
		# "payment_date": { "type": "string" },
		# "claimants":{
		# 	"type": "array",
		# 	"items": {
		# 		"type": "object",
		# 		"description": "line items grouped by Patient Name",
		# 		"properties":{
		# 			"patient_name": { "type": "string" },
		# 			"line_items": {
		# 				"type": "array",
		# 				"items": {
		# 					"type": "object",
		# 					"properties": {
		# 						"claim_number": { "type": "string" },
		# 						"service_date": { "type": "string" },
		# 						"service_description": { "type": "string" },
		# 						"claimed_amount": { "type": "number" },
		# 						"paid_amount": { "type": "number" }
		# 					}
		# 				}
		# 			},
		# 			"patient_total_claimed": { "type": "number", "description": "Total for Patient in Claimed" },
		# 			"patient_total_paid": { "type": "number", "description": "Total for Patient in Plan Paid" }
		# 		},
		# 		"required": []
		# 	}
		# }
		prompt = '''
			"payment_number": <Direct Deposit Number>,
			"payment_date": <DIRECT DEPOSIT STATEMENT date>,
			"claimants":
			[
				"policy_number": <Policy Number:>,
				"id_number": <ID Number:>,
				"patient_name": <Patient First Last Name>,
				"line_items": [
					{
						"claim_number": <Claim ID>,
						"service_date": <Service Date as dd/mm/YYYY>,
						"service_description": <service description>,
						"claimed_amount": <Claimed Amount>,
						"paid_amount": <Plan Paid Amount>"
					}
				],
				"total_claimed": <Total for Patient Claimed Amount>,
				"total_paid": <Total for Patient Plan Paid Amount>
			]
		'''
		if provider == SUNLIFE:
			system_msg = '''
			You are an insurance statement processing solution.
			Find claims grouped by Patient Name with Subtotals for Claimed Amount and Plan Paid Amount.
			Provide your answer in JSON formatted like so
			json schema=
			'''
			prompt = '''
				"payment_date": <Summary of Payment for Date>,
				"payment_number": <Deposit ID>,
				"claimants":
				[
					"policy_number": <Policy Number:>,
					"id_number": <ID Number:>,
					"patient_name": <Claimant initials>,
					"line_items": [
						{
							"claim_number": "<Claim ID / CPN>",
							"claimed_amount": <amount claimed>,
							"paid_amount": <amount reimbursed>"
						}
					]
				]
			'''
		elif provider == GREENSHIELD:
			system_msg = '''
			You are an insurance statement processing solution.
			Find claims grouped by Plan ID and Patient Name.
			Provide your answer in JSON.
			'''

			prompt = '''
			"payment_number": <EFT No.>,
			"payment_date": <Payment Date>,
			"patients":
			[
				"policy_number": <Claims for >,
				"patient_name": <formatted as First then Last Name>,
				"patient_claims": [
					{
						"claim_number": <Form Number>,
						"service_date": <Service Date as dd/mm/YYYY>,
						"service_description": <Claim Description>,
						"claimed_amount": <Claimed>,
						"paid_amount": <Paid>"
					}
				],
				"total_claimed": <Total for ID Claimed>,
				"total_paid": <Total for ID Paid>
			]
			'''
			# removed for now "id_number": <Plan member number>,
		elif provider == BLUECROSS:
			system_msg = '''
			You are an insurance statement processing solution.
			Find line-separated groups of claims for each Patient.
			Provide your answer in JSON.
			Format Dates as DD-MM-YYYY.
			'''
			#Ignor notes and codes at the bottom of grouped claims if present.
			#
			prompt = '''
				"payment_number": <Direct Deposit Number>,
				"payment_date": <DIRECT DEPOSIT STATEMENT date>,
				"patients":
				[
					"policy_number": <Policy Number>,
					"id_number": <ID Number>,
					"patient_name": <Patient First Last Name>,
					"patient_claims": [
						{
							"claim_number": <Claim ID>,
							"service_date": <Service Date as dd/mm/YYYY>,
							"service_description": <Service Description>,
							"claimed_amount": <Claimed Amount>,
							"paid_amount": <Plan Paid Amount>"
						}
					],
					"patient_total_claimed": <Total for Patient Claimed>,
					"patient_total_paid": <Total for Patient Plan Paid>
				]
			'''
		#system_msg += prompt
		return system_msg

	def get_statement_schema(self, provider):
		schema = {
			"type": "object",
			"properties":{
				"payment_number": { "type": "string" },
				"payment_date": { "type": "string" },
				"payment_amount": { "type": "number", "description": "Total payment amount" },
				# "unit": {
				# 	"type": "string",
				# 	"enum": ["grams", "ml", "cups", "pieces", "teaspoons"]
				# },
				"claimants":{
					"type": "array",
					"items": {
						"type": "object",
						"description": "line items grouped by Patient Name",
						"properties":{
							"patient_name": { "type": "string" },
							"line_items": {
								"type": "array",
								"items": {
									"type": "object",
									"properties": {
										"claim_number": { "type": "string" },
										"service_date": { "type": "string" },
										"service_description": { "type": "string" },
										"claimed_amount": { "type": "number" },
										"paid_amount": { "type": "number" }
									}
								}
							},
							"patient_total_claimed": { "type": "number", "description": "Total for Patient in Claimed" },
							"patient_total_paid": { "type": "number", "description": "Total for Patient in Plan Paid" }
						},
						"required": []
					}
				}
			},
			"required": ["payment_number", "claimants"]
		}
		if provider == BLUECROSS:
			schema = {
				"type": "object",
				"properties":{
					"payment_number": { "type": "string" },
					"payment_date": { "type": "string" },
					"payment_amount": { "type": "number", "description": "Total payment amount" },
					"patients": {
						"type": "array",
						"description": "list of grouped claims; each group starts with `Policy Number:` and ends with `Total for Patient`",
						"items": {
							"type": "object",
							"properties": {
								"policy_number": { "type": "string" },
								"id_number": { "type": "string" },
								"patient_name": { "type": "string",  "description": "Patient Name"},
								"patient_claims": {
									"type": "array",
									"description": "list of line items",
									"items": {
										"type": "object",
										"properties": {
											"claim_number": { "type": "string", "description": "Claim ID" },
											"service_date": { "type": "string", "description": "Service Date DD-MM-YYYY" },
											"service_description": { "type": "string", "description": "Product or Service" },
											"claimed_amount": { "type": "number" },
											"paid_amount": { "type": "number" }
										}
									}
								}
								# ,
								# "patient_total_claimed": { "type": "number", "description": "Total for Patient (first number) Claimed Amount" },
								# "patient_total_paid": { "type": "number", "description": "Total for Patient (second number) Plan Paid Amount`" }
							},
							"required": ["patient_claims"]
						}
					}
				},
				"required": ["payment_number", "patients"]
			}
		elif provider == GREENSHIELD:
			schema = {
			"type": "object",
			"properties":{
				"payment_number": { "type": "string" },
				"payment_date": { "type": "string" },
				"patients":{
					"type": "array",
					"items": {
						"type": "object",
						"description": "group of lines titled `Claims for `",
						"properties":{
							"patient_name": { "type": "string",  "description": "First Name follwed by Last Name"},
							"patient_claims": {
								"type": "array",
								"items": {
									"type": "object",
									"properties": {
										"claim_number": { "type": "string", "description": "Form Number" },
										"service_date": { "type": "string" },
										"service_description": { "type": "string" },
										"claimed_amount": { "type": "number" },
										"paid_amount": { "type": "number" }
									}
								}
							}
							# "patient_total_claimed": { "type": "number", "description": "Total for Patient in Claimed" },
							# "patient_total_paid": { "type": "number", "description": "Total for Patient in Plan Paid" }
						},
						"required": []
					}
				}
			},
			"required": ["payment_number", "patients"]
			}
		return schema

		'''
		cpn or empty string if not available,
		patient_name (also called claimant or plan member),
		and for each line item present in the claim -
			service_date (also called date or date of service) as dd/mm/YYYY,
			service_description,
			submitted_amount (also called submitted),
			total_paid (also called paid or paid amount).
		'''

	def get_claim_schema(self, provider):
		schema = {
			"type": "object",
			"properties":{
				"claim_number": { "type": "string", "description": "Claim ID"},
				"claim_submit_date:": { "type": "string", "description": "date in the top right corner" },
				"line_items":{
					"type": "array",
					"items": {
						"type": "object",
						"description": "rendered service lines items",
						"properties":{
							"patient_name": { "type": "string", "description": "Claimant"},
							"service_date": { "type": "string", "description": "Date of Service DD-MM-YYYY" },
							"service_description": { "type": "string" , "description": "Benefit" },
							"claimed_amount": { "type": "number", "description": "Submitted"},
							"paid_amount": { "type": "number", "description": "Amt Paid" }
						},
						"required": []
					}
				},
				"claim_total_claimed": { "type": "number", "description": "Total Submitted" },
				"claim_total_paid": { "type": "number", "description": "Total Paid" }
			},
			"required": ["claim_number", "line_items"]
		}
		return schema

	def request_ai(self, system_msg, user_msg, schema):
		# LOGGER.error(system_msg)
		# LOGGER.error('system_msg')
		# LOGGER.error(user_msg)
		# LOGGER.error('user_msg')
		# LOGGER.error(schema)
		# LOGGER.error('schema')

		response = self.client.chat.completions.create(
			model="gpt-3.5-turbo", #"gpt-4-turbo-preview "
			temperature=0,
			response_format={"type": "json_object"},
			messages=[
				{"role": "system", "content": system_msg},
				# { role: "user", content: "Who won the Premier League in 2020?" },
				# { role: "assistant", content: '{ "text": "Liverpool FC won the Premier League in 20.", "color": "red" }' },
				# { role: "user", content: "When is midnight?" },
				# { role: "assistant", content: '{ "text": "Midnight is at 00:00 or 12:00 AM", "color": "black" }' },
				# { role: "user", content: "When is easter?" },
				# { role: "assistant", content: '{ "text": "Easter is a moveable feast, meaning it is not fixed to a specific date each year. It typically falls on the first Sunday after the first full moon following the vernal equinox, which can range from March 22 to April 25.", "color": "yellow" }' },
				# { role: "user", content: "When is christmas eve?" },
				# { role: "assistant", content: '{ "text": "Christmas Eve is December 25th every year.", "color": "red" }' },
				{"role": "user", "content": user_msg}
			],
			functions=[{"name": "getPaymentData", "parameters": schema}],
			function_call={ "name": "getPaymentData" }
		)
		LOGGER.error('response')
		LOGGER.error(response)
		return self.get_response_data(response)

	def get_response_data(self, response, call_type='function'):
		data = {}
		try:
			if call_type == 'function': response_string = response.choices[0].message.function_call.arguments
			else: response_string = response.choices[0].message.content
			if response_string: data = json.loads(response_string)
		except Exception as e: LOGGER.error(e)
		return data

	def fetch_statement_data(self, file_text, provider, request):
		system_msg = self.get_statement_prompt(provider)
		schema = self.get_statement_schema(provider)

		query = '''Extract data from above statement.'''
		#extract data from above statement and return only the json containing the following -
		# 	insurance_provider (`unknown` if not found),
		# 	claim_number (called cpn or form number in the source document),
		# 	patient_name in `first name last name` format,
		# 	and for each line item present in the claim -
		# 		service_date (also called date or date of service) as dd/mm/YYYY,
		# 		service_description,
		# 		submitted_amount (called `amount claimed` in the source),
		# 		total_paid (called `amount reimbursed`).
		# patient_first_name, patient_last_name, reference_number,
		# service_date as dd/mm/YYYY, submitted_expense, eligible_expense, amount_paid -
		# for each line item present in the statement.
		# line_items=
		user_msg = file_text + '\n\n' + query
		data = self.request_ai(system_msg, user_msg, schema)

		if not data or 'patients' not in data: return data

		table_data, dataframe = [], {}
		dData = {'data': table_data, 'oData': data}
		doctype = 'statement'
		docnum 	= data['payment_number']
		for claimant in data['patients']:
			if 'patient_claims' not in claimant: continue
			for row in claimant['patient_claims']:
				cn = row.get('claim_number')
				pn = claimant.get('patient_name')
				sd = row.get('service_date')
				desc = row.get('service_description', '')
				ca = row.get('claimed_amount')
				pa = row.get('paid_amount')
				#key = slugify("{} {} {:.2f}".format(cn, pn, sd,))
				# index of duplicates or every line
				#key = slugify("{} {} {} {}".format(doctype, cn, sd, ca)) # todo: collect all the keys test if unique
				key = slugify("{} {} {}".format(cn, sd, ca))

				line = {
					'doctype': doctype,
					'provider': provider or UNKNOWN,
					'claim_number': cn,
					'patient_name': pn,
					'service_date': sd,
					'service_description': desc,
					'claimed_amount': ca,
					'paid_amount': pa,
					'status': '--',
					'key': key
				}
				table_data.append(line);
				dataframe[key] = line
		#table = df.to_json(orient='split', index=False)
		#user_statements = request.session.get(doctype, {})[docnum] = dataframe
		request.session[doctype] = {docnum: dataframe}

		return dData

	def fetch_claim_data(self, file_text, provider, request):
		system_msg = '''
		You are an insurance claim processing solution.
		Find claim details and provide your answer in JSON.
		Format Dates as DD-MM-YYYY.
		'''
		schema = self.get_claim_schema(provider)

		query = 'Extract data from the claim above.'
		user_msg = file_text + '\n\n' + query
		data = self.request_ai(system_msg, user_msg, schema)

		if not data: return # todo: add an exception

		table_data = []
		dData = {'data': table_data, 'oData': data}
		doctype = 'claim'
		user_statements = request.session.get('statement', {}).values() or []


		for row in data['line_items']:
			cn 		= data.get('claim_number', '')
			pn 		= row.get('patient_name', '') #data['patient_name']
			sd 		= row.get('service_date')
			desc 	= row.get('service_description', '')
			ca 		= row.get('claimed_amount', '')
			pa 		= row.get('paid_amount', '')
			tc 		= row.get('total_claimed')
			tp 		= row.get('total_paid')
			#key 	= slugify("{} {} {} {}".format(doctype, cn, sd, ca))
			key 	= slugify("{} {} {}".format(cn, sd, ca))
			status 	= 'new'

			for statement in user_statements:
				LOGGER.error('statement')
				status = 'not found {}'.format(key)
				# treatment has a matching row in a statement
				LOGGER.error('!!!!key {}'.format(key))
				if statement.get(key):
					status = '???'
					if statement.get(key).get('paid_amount') == pa:
						status = 'paid'

			table_data.append({
				'doctype': doctype,
				'provider': provider or UNKNOWN,
				'claim_number': cn,
				'patient_name': pn,
				'service_date': sd,
				'service_description': desc,
				'claimed_amount': ca,
				'paid_amount': pa,
				'status': status,
				'key': key
			})
		LOGGER.error('dData')
		LOGGER.error(dData)
		return dData

	def get_statement_line(self, data):
		user_statements = request.session['statement'].items() if request.session['statement'] else []
		for statement in user_statements:
			# treatment has a matching row in a statement
			if statement.get(key):
				if statement.get(key).get('paid_amount') == pa:
					status = 'paid'
				else: status = '???'



class InsuranceDocument():

	def __init__(self, file, request):
		self.driver 	= DriverFactory().get_driver()
		self._file 		= file.file.read() # POSTED file . todo - look into what is posted
		self.file 		= io.BytesIO(self._file)
		self.provider 	= self.get_provider()
		self.request = request

	def get_doctype(self):
		content = DataFactory().read_pdf(self.file)
		return self.driver.get_doctype(content) or UNKNOWN

	def get_provider(self):
		provider = None
		try:
			content = DataFactory().read_image(self._file) # TypeError: a bytes-like object is required, not '_io.BytesIO'
			provider = self.driver.get_insurance_provider(content)
			if not provider:
				content = DataFactory().read_pdf(self.file)
				provider = self.driver.get_insurance_provider(content)
		except Exception as e: LOGGER.error(e) #todo: add tracing
		return provider or UNKNOWN # or UNKNOWN?

	def read(self):
		# add try/catch
		content = DataFactory().read_pdf(self.file)
		doctype = self.get_doctype()

		if doctype == STATEMENT_TYPE: return self.driver.fetch_statement_data(content, self.provider, self.request)
		elif doctype == CLAIM_TYPE: return self.driver.fetch_claim_data(content, self.provider, self.request)
		return {}

class Statement(InsuranceDocument):

	def read(self):
		content = DataFactory().read_pdf(self.file)

		provider = OpenAIDriver().get_insurance_provider(content)
		return OpenAIDriver().get_statement_data(content)


class Invoice(InsuranceDocument):

	def read(self):
		content = DataFactory().read_pdf(self.file)
		# files = DataFactory().list_source_dir(self.source_dir)
		# data = []
		# content = ''
		# for f in files:
		# 	content += DataFactory().read_pdf(f) + '\n\n'
		return OpenAIDriver().get_invoice_data(content)

