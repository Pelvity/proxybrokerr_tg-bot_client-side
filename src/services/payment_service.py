# src/services/payment_service.py
from datetime import datetime, timedelta
from src.db.models.db_models import DBProxy, Payment, User
from src.utils.helpers import send_payment_confirmation_message_to_admin, send_payment_confirmation_message_to_user

def calculate_payment_amount(payment_period):
    # Example: Define different prices for different periods
    if payment_period == '1 week':
        return 10.0  # Example price
    elif payment_period == '1 month':
        return 35.0
    else:
        return 0.0

# src/services/payment_service.py
async def process_payment(user_id, proxy_ids, payment_period):
    user = User.get(User.id == user_id)
    amount = calculate_payment_amount(payment_period)

    for proxy_id in proxy_ids:
        proxy = DBProxy.get(DBProxy.id == proxy_id)
        payment = Payment.create(
            user=user,
            proxy=proxy,
            amount=amount,
            payment_date=datetime.now(),
            status='pending'  # Payment is initially pending admin confirmation
        )
        # Send a message to the admin for payment confirmation
        await send_payment_confirmation_message_to_admin(payment)


async def confirm_payment(payment_id):
    payment = Payment.get(Payment.id == payment_id)
    payment.status = 'confirmed'
    payment.save()

    # Update the proxy expiration date
    payment.proxy.expiration_date += timedelta(days=30)  # Assuming 1 month extension
    payment.proxy.save()

    # Notify the user about the payment confirmation
    await send_payment_confirmation_message_to_user(payment.user, payment)
