import os, io, logging
from pdfminer.high_level import extract_text, extract_text_to_fp
from pdfminer.layout import LAParams
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
			layout_controls = LAParams()
			extract_text_to_fp(file, output, laparams=layout_controls, output_type='text', codec=None)
			detected_text = output.getvalue()
			if include_images:
				image = pdf2image.convert_from_bytes(file)
				for pagenumber, page in enumerate(image):
					detected_text += pytesseract.image_to_string(page)
		except Exception as e: LOGGER.error(e, exc_info=True)

		return detected_text
