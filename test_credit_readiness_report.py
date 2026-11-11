import unittest

from pypdf import PdfReader
from io import BytesIO

from core.credit_readiness_report import build_credit_readiness_pdf


class CreditReadinessReportTests(unittest.TestCase):
    def setUp(self):
        self.result = {
            "status": "Further review recommended",
            "latest_month": "2026-11",
            "months_reviewed": ["2026-11", "2026-10", "2026-09"],
            "latest_cash_headroom": 5000.0,
            "average_three_month_headroom": 4200.0,
            "positive_headroom_months": 3,
            "proposed_monthly_emi": 1000.0,
            "headroom_after_proposed_emi": 4000.0,
            "coverage_proxy": 2.5,
            "revenue_change_percent": 4.2,
            "findings": ["No critical cash-headroom warning was identified."],
            "evidence_gaps": ["Credit bureau history was not assessed."],
            "limitations": "This is a simplified planning review.",
        }

    def test_generates_readable_pdf(self):
        data = build_credit_readiness_pdf("Sample Retail Shop", self.result)
        self.assertTrue(data.startswith(b"%PDF"))
        reader = PdfReader(BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("MSME Credit Readiness Review", text)
        self.assertIn("Sample Retail Shop", text)
        self.assertIn("Further review recommended", text)
        self.assertIn("Credit bureau history was not assessed.", text)

    def test_rejects_missing_business_name(self):
        with self.assertRaises(ValueError):
            build_credit_readiness_pdf(" ", self.result)

    def test_rejects_incomplete_assessment(self):
        with self.assertRaises(ValueError):
            build_credit_readiness_pdf("Sample Shop", {"status": "Review"})


