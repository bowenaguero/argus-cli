import ipaddress
import re
import sys
from pathlib import Path

import openpyxl
import PyPDF2


class FileParser:
    @staticmethod
    def extract_ips(text: str) -> list[str]:
        ips = set()
        for match in re.finditer(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", text):
            try:
                ip_obj = ipaddress.ip_address(match.group())
                if ip_obj.is_global:
                    ips.add(match.group())
            except ValueError:
                continue
        return sorted(ips)

    @staticmethod
    def read_pdf(filepath: str) -> str:
        if not PyPDF2:
            print("Error: PyPDF2 not installed. Run: pip install PyPDF2", file=sys.stderr)
            sys.exit(1)
        try:
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}", file=sys.stderr)
            sys.exit(1)
        else:
            return text

    @staticmethod
    def read_excel(filepath: str) -> str:
        if not openpyxl:
            print("Error: openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
            sys.exit(1)
        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            text = ""
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    for cell in row:
                        if cell:
                            text += str(cell) + " "
                    text += "\n"
        except Exception as e:
            print(f"Error reading Excel file: {e}", file=sys.stderr)
            sys.exit(1)
        else:
            return text

    @classmethod
    def read_file_content(cls, filepath: str) -> str:
        ext = Path(filepath).suffix.lower()

        if ext == ".pdf":
            return cls.read_pdf(filepath)
        elif ext in [".xlsx", ".xls"]:
            return cls.read_excel(filepath)
        else:
            try:
                with open(filepath) as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
