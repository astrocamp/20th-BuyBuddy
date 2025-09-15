import hashlib, binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib.parse
from django.shortcuts import render, get_object_or_404
from orders.models import Order, Payment
from django.utils import timezone
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

NEWEBPAY_MERCHANT_ID = settings.NEWEBPAY_MERCHANT_ID
NEWEBPAY_HASH_KEY = settings.NEWEBPAY_HASH_KEY
NEWEBPAY_HASH_IV = settings.NEWEBPAY_HASH_IV
NGROK_HOSTNAME = settings.NGROK_HOSTNAME
  
# 建立要送出給 藍新金流的資料
def create_payment_request(order, payment):
  order = get_object_or_404(Order, pk=order.id)
  payment = get_object_or_404(Payment, pk=payment.id)
  timestamp = str(int(timezone.now().timestamp()))
  # 1. 準備 TradeInfo 資料 
  trade_info = {
    "MerchantID": NEWEBPAY_MERCHANT_ID,
    "RespondType": "String",
    "TimeStamp": timestamp,
    "Version": "2.0",
    # 訂單編號
    "MerchantOrderNo": payment.payment_number,
    # 訂單金額
    "Amt": str(int(order.amount)),
    # 產品資訊
    "ItemDesc": order.group.name,
    # 回傳網址
    "ReturnURL": f"https://{NGROK_HOSTNAME}/orders/my-orders/payment/newebpay/return/",
    "NotifyURL": f"https://{NGROK_HOSTNAME}/orders/my-orders/payment/newebpay/notify/",
  }

  # 將 TradeInfo 轉換為 格式化字串
  query_string = urllib.parse.urlencode(trade_info)
  
  # 2. AES 加密
  trade_info_aes = aes_encrypt(query_string)
  
  # 3. SHA256 加密
  trade_info_sha = sha256_encrypt(trade_info_aes)
  

  payment_data = {
    "MerchantID": NEWEBPAY_MERCHANT_ID,
    "Version": "2.0",
    "TradeInfo": trade_info_aes,
    "TradeSha": trade_info_sha,
  }
  return payment_data

# AES-256-CBC 加密實作
def aes_encrypt(data):
  # 執行 AES 加密，使用 PKCS7 填充
  cipher = AES.new(
      NEWEBPAY_HASH_KEY.encode('utf-8'),
      AES.MODE_CBC,
      NEWEBPAY_HASH_IV.encode('utf-8')
  )

  # 填充至 16 bytes 的倍數
  padded_data = pad(data.encode('utf-8'), AES.block_size)
  encrypted_data = cipher.encrypt(padded_data)

  # 將加密結果轉換為十六進制並轉大寫
  aes_encrypt = encrypted_data.hex().upper()

  return aes_encrypt

# SHA256 加密實作 (格式: HashKey + TradeInfo + HashIV)
def sha256_encrypt(data):
  hash_str = f'HashKey={NEWEBPAY_HASH_KEY}&{data}&HashIV={NEWEBPAY_HASH_IV}'
  sha256_result = hashlib.sha256(hash_str.encode('utf-8')).hexdigest().upper()
  return sha256_result


# 解密 TradeInfo
def handle_newebpay_notify(request):
  tradeInfo = request.POST.get("TradeInfo")
  
  aes_tradeInfo = aes_decrypt(tradeInfo)

  parsed_tradeInfo = parse_tradeInfo(aes_tradeInfo)
  
  tradeInfo_data = {
    "status": parsed_tradeInfo.get("Status"),
    "merchant_order_no": parsed_tradeInfo.get("MerchantOrderNo"),
    "payment_type": parsed_tradeInfo.get("PaymentType"),
    "pay_time": parsed_tradeInfo.get("PayTime"),
    "message": parsed_tradeInfo.get("Message"),
  }

  return tradeInfo_data

# AES 解密
def aes_decrypt(tradeInfo):
  # 1. 將十六進制字符串轉為 bytes（對應 PHP 的 hex2bin）
  tradeInfo_bytes = binascii.unhexlify(tradeInfo)

  # 2. 建立 AES 解密器
  cipher = AES.new(
      NEWEBPAY_HASH_KEY.encode('utf-8'),
      AES.MODE_CBC,
      NEWEBPAY_HASH_IV.encode('utf-8')
  )

  # 3. 使用 AES 解密器 執行解密
  decrypted_data = cipher.decrypt(tradeInfo_bytes)


  # 4. 去除 PKCS7 填充
  decrypted_string = strip_pkcs7_padding(decrypted_data)
  

  return decrypted_string

# 去除 PKCS7 填充
def strip_pkcs7_padding(decrypted_data):

  if len(decrypted_data) == 0:
        return decrypted_data
    
  # 取得最後一個字節的值（填充長度）
  padding_length = decrypted_data[-1]
  
  # 檢查填充是否有效
  if padding_length > len(decrypted_data)or padding_length == 0:
      raise ValueError("Invalid PKCS7 padding")
      
  # 檢查填充字節是否正確
  padding_bytes = decrypted_data[-padding_length:]

  if not all(byte == padding_length for byte in padding_bytes):
      raise ValueError("Invalid PKCS7 padding")

  return decrypted_data[:-padding_length]


# 解析 TradeInfo
def parse_tradeInfo(aes_tradeInfo):
  # 1. 轉換為字符串（如果是 bytes）
  if isinstance(aes_tradeInfo, bytes):
      response_string = aes_tradeInfo.decode('utf-8')
  else:
      response_string = aes_tradeInfo

  # 2. URL 解碼 + 解析參數
  parsed_data = urllib.parse.parse_qs(response_string)
  
  # 3. parse_qs 回傳的值都是 list，取第一個元素
  result = {}
  for key, value_list in parsed_data.items():
      result[key] = value_list[0] if value_list else ''
  
  return result


