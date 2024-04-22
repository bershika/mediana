from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json, logging
from django.conf import settings

from .openAI import InsuranceDocument, Statement, Invoice

LOGGER = logging.getLogger(__name__)

def read_insurance_document(request):
	data = {}
	try:
		for f in request.FILES.getlist('files[]'):
			#data = Statement(f).get_provider()
			data = InsuranceDocument(f, request).read() or {}
	except Exception as e: LOGGER.error(e, exc_info=True)
	# for line in invoice:
	# 	key = line['key']
	# 	matched_row = next((row for row in data if row['key'] == key), None)
	# 	if matched_row: matched_row['invoice_number'] = line['invoice_number']
	return JsonResponse(data)

def read_statement(request):
	data = {}
	for f in request.FILES.getlist('files[]'):
		#data = Statement(f).get_provider()
		data = Statement(f).read()
	# for line in invoice:
	# 	key = line['key']
	# 	matched_row = next((row for row in data if row['key'] == key), None)
	# 	if matched_row: matched_row['invoice_number'] = line['invoice_number']
	return JsonResponse({'data': data})


@require_http_methods(["POST"])
def read_invoice(request):
	lines = []
	error = False
	result = True
	try:
		for f in request.FILES.getlist('files[]'):
			lines = Invoice(f).read()
			# for line in lines:
			# 	key = line['key']
			# 	matched_row = next((row for row in data if row['key'] == key), None)
			# 	if matched_row: matched_row['invoice_number'] = line['invoice_number']
	except Exception as e:
		error = str(e)
		raise e
	return JsonResponse({
		"success": result and not error,
		"data": lines,
		"error": error
	})
def parse_invoice(request):

	#invoice = Invoice().read()
	data = {}
	# for line in invoice:
	# 	key = line['key']
	# 	matched_row = next((row for row in data if row['key'] == key), None)
	# 	if matched_row: matched_row['invoice_number'] = line['invoice_number']
	return JsonResponse({'data': data})

def calc(request):
	LOGGER.error(settings.STATICFILES_DIRS)
	return render(request, "calc.html")

@require_http_methods(["POST"])
def signup(request):
	try:
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save(commit=False)
			user.is_active = False
			user.save()
			user = authenticate(
				username=form.cleaned_data['username'],
				password=form.cleaned_data['password2'],
			)
			if user is None:
				return JsonResponse({
					'result': False,
					'errors': json.dumps({'alert': ['Please allow 24 hours for your account to be activated.',]})
				})
			else:
				login(request, user)
				return JsonResponse({'result': True})
		else:
			data = json.dumps(dict(form.errors.items()), ensure_ascii=False)
			return JsonResponse({'result': False, 'errors': data}, safe=False)
	except Exception as e:
		LOGGER.error(e, exc_info=True)
		return JsonResponse({'result': False, 'errors': [str(e)]})

@require_http_methods(["POST"])
def signin(request):
	try:
		user = authenticate(
			username=request.POST["username"],
			password=request.POST["password"]
		)
		if user is not None:
			login(request, user)
			return JsonResponse({'result': True})
		return JsonResponse({'result': False})
	except Exception as e:
		LOGGER.error(e, exc_info=True)
		return JsonResponse({'result': False, 'errors': [str(e)]})



