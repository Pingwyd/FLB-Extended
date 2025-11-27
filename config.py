import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'flb.db')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Interswitch Configuration (Sandbox Defaults)
INTERSWITCH_MERCHANT_CODE = os.environ.get('INTERSWITCH_MERCHANT_CODE', 'MX6072')
INTERSWITCH_PAY_ITEM_ID = os.environ.get('INTERSWITCH_PAY_ITEM_ID', '9405967')
INTERSWITCH_PAYMENT_URL = os.environ.get('INTERSWITCH_PAYMENT_URL', 'https://newwebpay.qa.interswitchng.com/collections/w/pay')
INTERSWITCH_VERIFY_URL = os.environ.get('INTERSWITCH_VERIFY_URL', 'https://qa.interswitchng.com/collections/api/v1/gettransaction.json')

# Financial Configuration
WITHDRAWAL_FEE = 100.0  # NGN
DEPOSIT_FEE_PERCENTAGE = 0.015  # 1.5%
PLATFORM_COMMISSION_PERCENTAGE = 0.05  # 5%

