# src/repositories/payment_repository.py
from src.db.models.db_models import Payment, DBProxy
import logging

class PaymentRepository:
    def __init__(self, database):
        self.database = database

    async def create_payment(self, user, amount, status, proxies):
        payments = []
        try:
            with self.database.db.atomic():
                # Create a new payment record for each proxy
                for proxy in proxies:
                    payment = Payment.create(
                        user=user,
                        proxy=proxy,
                        amount=amount,
                        status=status
                    )
                    payments.append(payment)
                return payments
        except Exception as e:
            logging.exception(f"Error creating payment: {e}")
            return None

    async def update_payment_status(self, payment_id, new_status):
        try:
            with self.database.db.atomic():
                payment = Payment.get_by_id(payment_id)
                payment.status = new_status
                payment.save()
        except Exception as e:
            logging.exception(f"Error updating payment status: {e}")
            return None