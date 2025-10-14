# schema.py
schema_info = """
DATABASE SCHEMA INFORMATION

===========================================
TABLE 1: std_tran_kind
===========================================
Description: Standard transaction type master table defining various transaction categories like how the money was used for which can be called usage in pnlr_sumr_dtls table.

Columns:
  • tran_kind_cd (VARCHAR, PRIMARY KEY)
    Description: Unique transaction kind code.
  
  • tran_kind_nm (VARCHAR)
    Description: Transaction kind name in Korean.


===========================================
TABLE 2: selr_daly_sumr
===========================================
Description: This table is a Daily Customer Sales and Accounts Receivable Ledger, tracks a business's sales activity and the resulting cash flow status with its customers daily.

Columns:
  • use_intt_id (VARCHAR, PRIMARY KEY)
    Description: Unique Organizer or Institute ID.
  
  • trsc_dt (DATE, PRIMARY KEY)
    Description: Transaction Date in format YYYY-MM-DD.
  
  • bzaq_key (NUMERIC, PRIMARY KEY)
    Description: Business partner or customer or client key or account key.
  
  • sale_cnt (NUMERIC)
    Description: Number of sales.
  
  • sale_amt (NUMERIC)
    Description: Sale amount in KRW (South Korean Won) that comes from sply_amt + item_tax.
  
  • sply_amt (NUMERIC)
    Description: Supply price or amount before tax in KRW (South Korean Won).
  
  • item_tax (NUMERIC)
    Description: Additional tax amount in KRW (South Korean Won).
  
  • ctmn_amt (NUMERIC)
    Description: Amount Collected or Collection of Money in KRW (South Korean Won).
  
  • rcbl_bal (NUMERIC)
    Description: Outstanding Receivable Balance, the money that business partner or customer or client still owes in KRW (South Korean Won).
  
  • cmlt_sale_cnt (NUMERIC)
    Description: Total number of sales transactions recorded for this business partner or customer or client up to and including the Transaction Date.
  
  • cmlt_sale_amt (NUMERIC)
    Description: Total value of all sales recorded for this business partner or customer or client up to and including the Transaction Date in KRW (South Korean Won).
  
  • cmlt_ctmn_amt (NUMERIC)
    Description: Total amount of money collected from this business partner or customer or client up to and including the Transaction Date in KRW (South Korean Won).
  
  • cmlt_ctmn_cnt (NUMERIC)
    Description: Total number of collection transactions recorded for this business partner or customer or client up to and including the Transaction Date.
  
  • ctmn_cnt (NUMERIC)
    Description: Number of collection transactions made by the business partner or customer or client on the Transaction Date.


===========================================
TABLE 3: selr_mnly_sumr
===========================================
Description: This table is a Monthly Customer Sales and Accounts Receivable.

Columns:
  • use_intt_id (VARCHAR, PRIMARY KEY)
    Description: Unique Organizer or Institute ID.
  
  • trsc_ym (VARCHAR, PRIMARY KEY)
    Description: Transaction Date containing only year and month in format YYYYMM.
  
  • bzaq_key (NUMERIC, PRIMARY KEY)
    Description: Business partner or customer or client key or account key.
  
  • sale_cnt (NUMERIC)
    Description: Number of sales.
  
  • sale_amt (NUMERIC)
    Description: Sale amount in KRW (South Korean Won) that get from sply_amt + item_tax.
  
  • sply_amt (NUMERIC)
    Description: Supply price or amount before tax in KRW (South Korean Won).
  
  • item_tax (NUMERIC)
    Description: Additional tax amount in KRW (South Korean Won).
  
  • ctmn_amt (NUMERIC)
    Description: Amount Collected or Collection of Money in KRW (South Korean Won).
  
  • rcbl_bal (NUMERIC)
    Description: Outstanding Receivable Balance, the money that business partner or customer or client still owes in KRW (South Korean Won).


===========================================
TABLE 4: buyr_daly_sumr
===========================================
Description: This table is a Daily Supplier Purchases and Accounts Payable Ledger, tracks a business's purchases activity and the resulting cash flow status with its customers monthly.

Columns:
  • use_intt_id (VARCHAR, PRIMARY KEY)
    Description: Unique Organizer or Institute ID.
  
  • trsc_dt (VARCHAR, PRIMARY KEY)
    Description: Transaction Date in format YYYYMMDD.
  
  • bzaq_key (NUMERIC, PRIMARY KEY)
    Description: Business partner or customer or client key or account key.
  
  • buy_cnt (NUMERIC)
    Description: Number of purchases.
  
  • buy_amt (NUMERIC)
    Description: Purchases amount in KRW (South Korean Won) that get from sply_amt + item_tax.
  
  • sply_amt (NUMERIC)
    Description: Supply price or amount before tax in KRW (South Korean Won).
  
  • item_tax (NUMERIC)
    Description: Additional tax amount in KRW (South Korean Won).
  
  • paym_amt (NUMERIC)
    Description: Amount Paid or Payment of Money to the supplier or business partner in KRW (South Korean Won).
  
  • upay_bal (NUMERIC)
    Description: Outstanding Unpaid Balance, the money that institute or organizer still owes supplier or business partner in KRW (South Korean Won).
  
  • cmlt_buy_cnt (NUMERIC)
    Description: Total number of purchase transactions recorded for this institute or organizer up to and including the Transaction Date.
  
  • cmlt_buy_amt (NUMERIC)
    Description: Total value of all purchases recorded for this institute or organizer up to and including the Transaction Date in KRW (South Korean Won).
  
  • cmlt_paym_amt (NUMERIC)
    Description: Total amount of money paid to the supplier or business partner up to and including the Transaction Date in KRW (South Korean Won).
  
  • cmlt_paym_cnt (NUMERIC)
    Description: Total number of payment transactions recorded for this institute or organizer up to and including the Transaction Date.
  
  • paym_cnt (NUMERIC)
    Description: Number of payment transactions made by institute or organizer on the Transaction Date.


===========================================
TABLE 5: buyr_mnly_sumr
===========================================
Description: This table is a Monthly Supplier Purchases and Accounts Payable.

Columns:
  • use_intt_id (VARCHAR, PRIMARY KEY)
    Description: Unique Organizer or Institute ID.
  
  • trsc_ym (VARCHAR, PRIMARY KEY)
    Description: Transaction Date containing only year and month in format YYYYMM.
  
  • bzaq_key (NUMERIC, PRIMARY KEY)
    Description: Business partner or customer or client key or account key.
  
  • buy_cnt (NUMERIC)
    Description: Number of purchases.
  
  • buy_amt (NUMERIC)
    Description: Purchases amount in KRW (South Korean Won) that get from sply_amt + item_tax.
  
  • sply_amt (NUMERIC)
    Description: Supply price or amount before tax in KRW (South Korean Won).
  
  • item_tax (NUMERIC)
    Description: Additional tax amount in KRW (South Korean Won).
  
  • paym_amt (NUMERIC)
    Description: Amount Paid or Payment of Money to the supplier or business partner in KRW (South Korean Won).
  
  • upay_bal (NUMERIC)
    Description: Outstanding Unpaid Balance, the money that institute or organizer still owes supplier or business partner in KRW (South Korean Won).


===========================================
TABLE 6: pnlr_sumr_dtls
===========================================
Description: This table is about aggregating all business transactions (whether sales or purchases) based on what the money was used for and what kind of legal documentation proves the transaction.

Columns:
  • use_intt_id (VARCHAR, PRIMARY KEY)
    Description: Unique Organizer or Institute ID.
  
  • use_usag_cd (VARCHAR, PRIMARY KEY)
    Description: Transaction kind name or usage purpose.
  
  • trsc_dt (DATE, PRIMARY KEY)
    Description: Transaction Date in format YYYYMMDD.
  
  • evdc_dv (VARCHAR)
    Description: Evidence type of the transaction (e.g., tax invoice, cash receipt etc.)
  
  • bzaq_key (NUMERIC)
    Description: Business partner or customer or client key or account key.
  
  • sply_amt (NUMERIC)
    Description: Supply price or amount before tax in KRW (South Korean Won).
  
  • item_tax (NUMERIC)
    Description: Additional tax amount in KRW (South Korean Won).
  
  • trsc_amt (NUMERIC)
    Description: The total value of the transaction, calculated as Net Amount + Tax Amount in KRW (South Korean Won).


===========================================
TABLE 7: pnlr_daly_sumr
===========================================
Description: This table is about daily aggregation of profit and loss report based on rpt_grp_cd1, rpt_grp_cd2 and use_usag_cd.

Columns:
  • use_intt_id (VARCHAR, PRIMARY KEY)
    Description: Unique Organizer or Institute ID.
  
  • rpt_grp_cd1 (VARCHAR, PRIMARY KEY)
    Description: Report Group Code 1 main group.
  
  • rpt_grp_cd2 (VARCHAR, PRIMARY KEY)
    Description: Report Group Code 2 secondary group.
  
  • use_usag_cd (VARCHAR, PRIMARY KEY)
    Description: Transaction kind name or usage purpose.
  
  • sumr_dt (VARCHAR, PRIMARY KEY)
    Description: Date of the daily summed up transactions in format YYYYMMDD.
  
  • sumr_sply_amt (NUMERIC)
    Description: Total amount of supply in KRW (South Korean Won) before tax.
  
  • sumr_item_tax (NUMERIC)
    Description: Total Additional tax amount in KRW (South Korean Won).
  
  • sumr_amt (NUMERIC)
    Description: Total amount that from sumr_sply_amt + sumr_item_tax.


===========================================
TABLE 8: pnlr_mnly_sumr
===========================================
Description: This table is about Monthly aggregation of profit and loss reports based on rpt_grp_cd1, rpt_grp_cd2 and use_usag_cd.

Columns:
  • use_intt_id (VARCHAR, PRIMARY KEY)
    Description: Unique Organizer or Institute ID.
  
  • rpt_grp_cd1 (VARCHAR, PRIMARY KEY)
    Description: Report Group Code 1.
  
  • rpt_grp_cd2 (VARCHAR, PRIMARY KEY)
    Description: Report Group Code 2.
  
  • use_usag_cd (VARCHAR, PRIMARY KEY)
    Description: Transaction kind name or usage purpose.
  
  • sumr_ym (VARCHAR, PRIMARY KEY)
    Description: Date of the monthly summed up transactions in format YYYYMM.
  
  • sumr_sply_amt (NUMERIC)
    Description: Total amount of supply in KRW (South Korean Won) before tax.
  
  • sumr_item_tax (NUMERIC)
    Description: Total Additional tax amount in KRW (South Korean Won).
  
  • sumr_amt (NUMERIC)
    Description: Total amount that from sumr_sply_amt + sumr_item_tax.


===========================================
TABLE 9: rprt_bzaq_infm
===========================================
Description: This a master table is about Report account information based on use_intt_id, bzaq_key.

Columns:
  • use_intt_id (VARCHAR, PRIMARY KEY)
    Description: Unique Organizer or Institute ID.
  
  • bzaq_key (NUMERIC, PRIMARY KEY)
    Description: Unique business partner or customer or client key or account key.
  
  • bzaq_nm (VARCHAR)
    Description: Unique business partner or customer or client name or account name.


===========================================
TABLE 10: dsdl_item
===========================================
Description: This a master table that manages group code information used by pnlr_mnly_sumr and pnlr_daly_sumr.

Columns:
  • dsdl_grp_cd (VARCHAR, PRIMARY KEY)
    Description: Unique group code.
  
  • dsdl_item_cd (VARCHAR, PRIMARY KEY)
    Description: Unique item code that specifies Accounting Classifications or Account Titles like Revenue, Expense, Assets, and Liabilities.
  
  • dsdl_item_nm (VARCHAR)
    Description: Name of the item code.
  
  • dsdl_item_vw_nm (VARCHAR)
    Description: Item code display name.
  
  • dsdl_desc (VARCHAR)
    Description: Item code description.
  
  • use_yn (VARCHAR)
    Description: Use status with Y for yes and N for no.
  
  • otpt_sqnc (VARCHAR)
    Description: Output Order / Display Order numerical value specifying the preferred sorting sequence when presenting the items.

"""
