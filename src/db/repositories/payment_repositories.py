from datetime import datetime, timedelta
from src.db.models.db_models import CryptoPayment, Payment, DBProxyConnection

class PaymentRepository:
    def __init__(self, session):
        self.session = session

    def create_payments(self, user, payment_items, txid, days, payment_method):
        """Creates multiple Payment records and updates proxy connection expiration dates."""
        payments = []
        try:
            for connection, amount in payment_items:
                start_date = connection.expiration_date.date() if connection.expiration_date else datetime.now().date()
                end_date = start_date + timedelta(days=days)

                payment = Payment(
                    user_id=user.id,
                    connection_id=connection.id,
                    amount=amount,
                    payment_date=datetime.now(),
                    status='pending',
                    payment_method=payment_method,
                    start_date=start_date,
                    end_date=end_date
                )
                payments.append(payment)
                self.session.add(payment)

            self.session.commit()
            return payments

        except Exception as e:
            print(f"Error creating payments: {e}")
            self.session.rollback()
            return None

    def get_payment_by_id(self, payment_id: int) -> Payment:
        """Gets a payment by its ID."""
        return self.session.query(Payment).get(payment_id)

    def confirm_payment(self, payment: Payment, txid: str):
        """Confirms a payment and extends the proxy connection expiration date."""
        if payment.status != 'confirmed':
            payment.status = 'confirmed'
            connection = payment.connection
            connection.expiration_date = payment.end_date

            # Handle CryptoPayment
            if payment.payment_method == 'crypto':
                crypto_payment = self.session.query(CryptoPayment).filter_by(payment_id=payment.id).first()
                if not crypto_payment:
                    crypto_payment = CryptoPayment(payment_id=payment.id, txid=txid)
                    self.session.add(crypto_payment)
                else:
                    crypto_payment.txid = txid

            self.session.commit()




    def decline_payment(self, payment: Payment):
        """Declines a payment and handles associated records."""
        payment.status = 'declined'

        # Handle CryptoPayment
        if payment.payment_method == 'crypto':
            crypto_payment = self.session.query(CryptoPayment).filter_by(payment_id=payment.id).first()
            if crypto_payment:
                self.session.delete(crypto_payment)

        self.session.commit()


