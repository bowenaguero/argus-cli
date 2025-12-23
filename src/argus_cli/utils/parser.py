import ipaddress
import re
import sys
from pathlib import Path

import openpyxl
import pypdf


class FileParser:
    @staticmethod
    def expand_cidr(cidr: str) -> list[str]:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            msg = f"Invalid CIDR block: {cidr}"
            raise ValueError(msg) from e

        if network.num_addresses > 1024:
            msg = f"CIDR block {cidr} too large (max 1024 IPs)"
            raise ValueError(msg)

        return [str(ip) for ip in network.hosts() if ipaddress.ip_address(ip).is_global]

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
        if not pypdf:
            print("Error: pypdf not installed. Run: pip install pypdf", file=sys.stderr)
            sys.exit(1)
        try:
            with open(filepath, "rb") as f:
                reader = pypdf.PdfReader(f)
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
            print(
                "Error: openpyxl not installed. Run: pip install openpyxl",
                file=sys.stderr,
            )
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
