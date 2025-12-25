FINAL SALES / RETURN / EXCHANGE SYSTEM DESIGN
===========================================

CORE PRINCIPLE
--------------
- Original sales invoices are immutable
- Returns and exchanges are adjustments linked to original invoices
- Net Sale is a calculated state, not a separate transaction
- One Sales Ledger is the single source of truth


TRANSACTION WINDOWS (INPUT ONLY)
--------------------------------

1) sales.py — Original Sale Entry
- Records original sales invoices
- Generates INV-XXXXX
- Deducts inventory
- Saves:
  - Items
  - Quantities
  - Prices
  - Discount
  - Grand Total
- No return or exchange logic exists here


2) sales_return.py — Return Entry
- Records return transactions against an existing invoice
- Generates:
  RTN-INV-XXXXX-1
  RTN-INV-XXXXX-2
- User selects:
  - Original invoice number
  - Returned items
  - Returned quantities
- Inventory is restocked
- Return Fee:
  - Default loaded from settings
  - Editable per return
  - Can be zero
  - Stored per return record
- Prints Return Invoice:
  - Only returned items
  - Reference to original invoice
  - Return amount
  - Return fee (if applied)


3) sales_exchange.py — Exchange Entry
- Exchange is treated as:
  Return + New Sale
- Steps:
  1) Record returned items
  2) Record issued items
- Generates:
  EX-INV-XXXXX-1
- Prints Exchange Invoice:
  - Returned items
  - Issued items
  - Price difference
  - Return fee (if any)
  - Final payable or refundable amount


SALES LEDGER (SINGLE HISTORY WINDOW)
-----------------------------------

sales_ledger.py — Master Sales Ledger

This replaces:
- sales_history.py
- sales_return_history.py
- sales_exchange_history.py
- net_sale.py
- net_invoice.py

Purpose:
- Show all invoices
- Show real-time calculated net values
- Provide all printing options

Columns:
- Invoice No
- Date
- Customer
- Gross Qty
- Gross Amount
- Returned Qty
- Returned Amount
- Exchanged Amount
- Net Qty
- Net Amount
- Status

Status Values:
- NORMAL
- PARTIAL RETURN
- FULL RETURN
- EXCHANGE

Net Calculations:
- Net Qty    = Gross Qty - Returned Qty + Exchange Issued Qty
- Net Amount = Gross Amount - Returned Amount + Exchange Amount - Return Fees


PRINTING OPTIONS (FROM SALES LEDGER)
-----------------------------------

From a selected invoice:
1) Print Original Invoice
2) Print Return Invoice(s)
3) Print Exchange Invoice(s)
4) Print Net Invoice


NET INVOICE (PRINT MODE ONLY)
----------------------------

- Not a separate window
- Not a separate invoice number
- Uses original invoice number
- Header:
  NET INVOICE
  Based on Original Invoice: INV-XXXXX
- Shows:
  - Only final items
  - Only net quantities
  - Net totals
- Does NOT show returned or exchanged items


TERMS & CONDITIONS HANDLING
---------------------------

- Return fee terms appear only if a return fee is applied
- Terms are appended dynamically
- No return terms appear on invoices without returns


REPORTS / DASHBOARD
-------------------

- Uses net values from Sales Ledger
- Accurate for:
  - Revenue
  - Inventory movement
  - Profit
- Supports:
  - Daily
  - Weekly
  - Monthly
  - Yearly


FINAL TRUTH STATEMENT
--------------------

If a window does not create a new transaction,
it should not exist as a separate history window.

This design is:
- Audit-safe
- Scalable
- Professionally correct
- Free of duplicated logic
- Easy to maintain
