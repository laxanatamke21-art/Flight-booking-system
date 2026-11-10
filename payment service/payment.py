from braintree_config import gateway


# ==========================================
# GENERATE BRAINTREE CLIENT TOKEN
# ==========================================

def generate_client_token():
    try:
        print("====================================")
        print("🔐 Generating Braintree Client Token")
        print("====================================")

        client_token = gateway.client_token.generate()

        print("✅ Client token generated successfully")

        return {
            "success": True,
            "client_token": client_token
        }

    except Exception as e:
        print("❌ Braintree client token error")
        print("Error type:", type(e).__name__)
        print("Error:", repr(e))

        return {
            "success": False,
            "message": str(e) if str(e) else repr(e)
        }


# ==========================================
# PROCESS BRAINTREE PAYMENT
# ==========================================

def process_payment(
    amount,
    payment_method_nonce,
    booking_id=None,
    device_data=None
):
    try:
        print("====================================")
        print("💳 Processing Braintree Payment")
        print("====================================")

        # Validate amount
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "Invalid payment amount"
            }

        if amount <= 0:
            return {
                "success": False,
                "message": "Payment amount must be greater than 0"
            }

        # Validate nonce
        if not payment_method_nonce:
            return {
                "success": False,
                "message": "Braintree payment nonce is required"
            }

        # Transaction data
        transaction_data = {
            "amount": f"{amount:.2f}",
            "payment_method_nonce": payment_method_nonce,
            "options": {
                "submit_for_settlement": True
            }
        }

        # Add booking ID as order ID
        if booking_id:
            transaction_data["order_id"] = str(booking_id)

        # Add device data if available
        if device_data:
            transaction_data["device_data"] = device_data

        # Send transaction to Braintree
        result = gateway.transaction.sale(transaction_data)

        print("Braintree transaction result received")

        # Successful payment
        if result.is_success:
            transaction = result.transaction

            print("✅ Braintree payment successful")
            print("Transaction ID:", transaction.id)
            print("Status:", transaction.status)

            return {
                "success": True,
                "transaction_id": transaction.id,
                "status": transaction.status,
                "message": "Braintree payment successful"
            }

        # Failed payment
        print("❌ Braintree payment failed")
        print("Message:", result.message)

        return {
            "success": False,
            "message": result.message or "Braintree payment failed"
        }

    except Exception as e:
        print("❌ Braintree payment exception")
        print("Error type:", type(e).__name__)
        print("Error:", repr(e))

        return {
            "success": False,
            "message": str(e) if str(e) else repr(e)
        }