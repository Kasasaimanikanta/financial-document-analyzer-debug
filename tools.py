## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()
import pdfplumber

class Pdf:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        pages = []
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    class Page:
                        def __init__(self, content):
                            self.page_content = content
                    pages.append(Page(text))

        return pages  # ← VERY IMPORTANT (must return list)

from crewai_tools import SerperDevTool

## Creating search tool
search_tool = SerperDevTool()


# Import BaseTool and Pdf (add placeholder if Pdf is missing)
from crewai.tools import BaseTool
# try:
#     from some_pdf_library import Pdf  # Replace with actual PDF library if available
# except ImportError:
# class Pdf:
#     def __init__(self, file_path):
#         self.file_path = file_path
#     def load(self):
#         # Placeholder: returns a list of objects with page_content attribute
#         class Page:
#             def __init__(self, content):
#                 self.page_content = content
#         return [Page("Sample PDF content from " + self.file_path)]



class FinancialDocumentTool(BaseTool):
    name: str = "Financial Document Reader"
    description: str = "Reads and extracts text from a financial PDF document."

    # def _run(self, file_path='data/sample.pdf', query=None, **kwargs):
    def _run(self, file_path: str, **kwargs):
        docs = Pdf(file_path=file_path).load()
        full_report = ""
        for data in docs:
            content = data.page_content
            while "\n\n" in content:
                content = content.replace("\n\n", "\n")
            full_report += content + "\n"
        return full_report

# Instantiate the tool
financial_document_tool = FinancialDocumentTool()

## Creating Investment Analysis Tool
class InvestmentTool:
    async def analyze_investment_tool(financial_document_data):
        # Process and analyze the financial document data
        processed_data = financial_document_data
        
        # Clean up the data format
        i = 0
        while i < len(processed_data):
            if processed_data[i:i+2] == "  ":  # Remove double spaces
                processed_data = processed_data[:i] + processed_data[i+1:]
            else:
                i += 1
                
        # TODO: Implement investment analysis logic here
        return "Investment analysis functionality to be implemented"

## Creating Risk Assessment Tool
class RiskTool:
    async def create_risk_assessment_tool(financial_document_data):        
        # TODO: Implement risk assessment logic here
        return "Risk assessment functionality to be implemented"