#!/usr/bin/env python3
"""Normalize SEC companyfacts into fiscal-year metrics."""
import argparse,csv,gzip,json
from pathlib import Path
from collections import Counter
from datetime import date
TAGS={
'revenue':['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet'],
'gross_profit':['GrossProfit'],'operating_income':['OperatingIncomeLoss'],
'net_income':['NetIncomeLoss'],'eps_diluted':['EarningsPerShareDiluted'],
'cfo':['NetCashProvidedByUsedInOperatingActivities'],
'capex':['PaymentsToAcquirePropertyPlantAndEquipment'],
'assets':['Assets'],'equity':['StockholdersEquity'],
'cash':['CashAndCashEquivalentsAtCarryingValue'],
'debt_noncurrent':['LongTermDebtNoncurrent'],'debt_total_reported':['LongTermDebt'],
'debt_current':['LongTermDebtCurrent'],'short_borrowings':['ShortTermBorrowings'],
'interest_expense':['InterestExpenseNonOperating','InterestExpense'],
'depreciation_amortization':['DepreciationDepletionAndAmortization'],
'pretax_income':['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'],
'tax_expense':['IncomeTaxExpenseBenefit']}
