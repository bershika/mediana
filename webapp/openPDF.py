import os, io
import logging
#import PyPDF2
#from pdfminer.high_level import extract_text as fallback_text_extraction
from pdfminer.high_level import extract_text, extract_text_to_fp
from pdfminer.layout import LAParams

from django.conf import settings

import pdf2image
from PIL import Image
import pytesseract

LOGGER = logging.getLogger(__name__)

class DataFactory:

	def list_source_dir(self, source_dir):
		return [os.path.join(source_dir, file_name) for file_name in os.listdir(source_dir) if file_name.endswith('.pdf')]

	def read_image(self, file):
		detected_text = ''
		image = pdf2image.convert_from_bytes(file)
		for pagenumber, page in enumerate(image):
			detected_text += pytesseract.image_to_string(page)
		return detected_text

	def read_pdf(self, file, include_images=False):
		detected_text = ''
		output = io.StringIO()
		try:
			#detected_text = extract_text(file)
			layout_controls = LAParams(
				# line_overlap = 0.5,
				# char_margin = 2,
				# line_margin = 0.5,
				# word_margin = 0.1,
				# boxes_flow = 0.5,
				# detect_vertical = False,
				# all_texts = False
			)
			extract_text_to_fp(file, output, laparams=layout_controls, output_type='text', codec=None)
			detected_text = output.getvalue()
			if include_images:
				image = pdf2image.convert_from_bytes(file)
				for pagenumber, page in enumerate(image):
					detected_text += pytesseract.image_to_string(page)

			# pdf_reader = PyPDF2.PdfReader(file)
			# num_pages = len(pdf_reader.pages)
			# for page_num in range(num_pages):
			# 	page_obj = pdf_reader.pages[page_num]
			# 	detected_text += page_obj.extract_text() + '\n\n'
			# 	if include_images:
			# 		try: detected_text += pytesseract.image_to_string(page_obj)
			# 		except Exception as e: LOGGER.error(e)
			#LOGGER.error(detected_text)
		except Exception as e: LOGGER.error(e, exc_info=True)

		return detected_text
