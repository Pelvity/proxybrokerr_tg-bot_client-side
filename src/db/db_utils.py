# from datetime import datetime, timezone
# from src.db.models.db_models import DBProxy, DBProxyConnection, ConnectionHistory
# from src.db.azure_db import AzureSQLService

# database_service = AzureSQLService()

# def create_proxy(proxy_data, phone_id, user_id):
#     """Creates a new Proxy and associates it with a Phone and User."""
#     with database_service.connect() as session:
#         new_proxy = DBProxy(
#             phone_id=phone_id,
#             user_id=user_id,
#             name=proxy_data.get("name"),
#             auth_token=proxy_data.get("auth_token"),
#             expiration_date=proxy_data.get("expiration_date"),
#             #hours_left=proxy_data.get("hours_left"),
#             tariff_plan=proxy_data.get("tariff_plan"),
#             tariff_expiration_date=proxy_data.get("tariff_expiration_date"),
#             tariff_days_left=proxy_data.get("tariff_days_left"),
#             device_model=proxy_data.get("device_model"),
#             active=proxy_data.get("active"),
#             service_name=proxy_data.get("service_name"),
#             service_account_login=proxy_data.get("service_account_login")
#         )
#         session.add(new_proxy)
#         session.commit()
#         return new_proxy

# def create_proxy_connection(proxy_id, user_id, connection_data):
#     """Creates a new ProxyConnection and its initial ConnectionHistory record."""
#     with database_service.connect() as session:
#         new_connection = DBProxyConnection(
#             proxy_id=proxy_id,
#             user_id=user_id,
#             name=connection_data.get("name"),
#             description=connection_data.get("description"),
#             host=connection_data.get("host"),
#             port=connection_data.get("port"),
#             login=connection_data.get("login"),
#             password=connection_data.get("password"),
#             connection_type=connection_data.get("connection_type")
#         )
#         session.add(new_connection)
#         session.commit()

#         # Create the initial ConnectionHistory record
#         create_connection_history(new_connection.id, connection_data, session)
#         return new_connection

# def update_proxy_connection(connection_id, connection_data):
#     """
#     Updates a ProxyConnection and creates a new ConnectionHistory record 
#     if any relevant connection details have changed.
#     """

#     with database_service.connect() as session:
#         connection = session.query(DBProxyConnection).get(connection_id)

#         if connection:
#             # 1. Check if any relevant fields have changed
#             has_changed = any([
#                 connection.host != connection_data.get('host'),
#                 connection.port != connection_data.get('port'),
#                 connection.login != connection_data.get('login'),
#                 connection.password != connection_data.get('password'),
#                 connection.name != connection_data.get("name"),
#                 connection.description != connection_data.get("description"),
#                 connection.connection_type != connection_data.get("connection_type")
#             ])

#             if has_changed:
#                 # 2. Create a new ConnectionHistory record 
#                 create_connection_history(connection.id, connection_data, session)

#                 # 3. Update the connection with the new data
#                 for key, value in connection_data.items():
#                     setattr(connection, key, value)

#                 connection.updated_timestamp = datetime.now(timezone.utc)
#                 session.commit()

# # def create_connection_history(connection_id, connection_data, session):
# #     """Creates a new ConnectionHistory record, closing the previous one."""
    
# #     # 1. End the previous history record (if any)
# #     previous_history = session.query(ConnectionHistory).filter_by(
# #         connection_id=connection_id, 
# #         end_datetime=None 
# #     ).first()
# #     if previous_history:
# #         previous_history.end_datetime = datetime.now(timezone.utc)
# #         session.commit()  # Commit the changes to close the previous history

# #     # 2. Create the new history record
# #     new_history = ConnectionHistory(
# #         connection_id=connection_id,
# #         host=connection_data.get('host'),
# #         port=connection_data.get('port'),
# #         login=connection_data.get('login'),
# #         password=connection_data.get('password'),
# #         name=connection_data.get("name"),
# #         description=connection_data.get("description"),
# #         connection_type=connection_data.get("connection_type"),
# #         start_datetime=datetime.now(timezone.utc)
# #     )
# #     session.add(new_history)
# #     session.commit()
    

# def update_proxy(db_proxy, proxy_data, session):
#     """Updates an existing Proxy record with new data."""
#     db_proxy.name = proxy_data.get("name")
#     db_proxy.user_id = proxy_data.get("user_id")
#     db_proxy.tariff_plan = proxy_data.get("tariff_plan")
#     db_proxy.tariff_expiration_date = proxy_data.get("tariff_expiration_date")
#     #db_proxy.days_left = proxy_data.get("days_left")
#     #db_proxy.hours_left = proxy_data.get("hours_left")
#     db_proxy.device_model = proxy_data.get("device_model")
#     db_proxy.active = proxy_data.get("active")
    
#     session.add(db_proxy)
#     session.commit()

# def update_connection(connection_id, connection_data):
#     """Updates a ProxyConnection and creates a new ConnectionHistory record 
#     if any relevant connection details have changed.
#     """

#     with database_service.connect() as session:
#         connection = session.query(DBProxyConnection).get(connection_id)

#         if connection:
#             # Check if any relevant fields have changed
#             has_changed = any([
#                 connection.host != connection_data.get('host'),
#                 connection.port != connection_data.get('port'),
#                 connection.login != connection_data.get('login'),
#                 connection.password != connection_data.get('password'),
#                 connection.name != connection_data.get("name"),
#                 connection.description != connection_data.get("description"),
#                 connection.connection_type != connection_data.get("connection_type")
#             ])

#             if has_changed:
#                 # Create a new ConnectionHistory record 
#                 create_connection_history(connection.id, connection_data, session)

#                 connection.host = connection_data.get('host')
#                 connection.port = connection_data.get('port')
#                 connection.login = connection_data.get('login')
#                 connection.password = connection_data.get('password')
#                 connection.name = connection_data.get("name")
#                 connection.description = connection_data.get("description")
#                 connection.connection_type = connection_data.get("connection_type")

#                 connection.updated_timestamp = datetime.now(timezone.utc)
#                 session.commit()
                
                
# def create_connection_history(connection_id, connection_data, session):
#     """Creates a new ConnectionHistory record, closing the previous one."""

#     # End the previous history record (if any)
#     previous_history = session.query(ConnectionHistory).filter_by(
#         connection_id=connection_id,
#         end_datetime=None
#     ).order_by(ConnectionHistory.start_datetime.desc()).first()

#     if previous_history:
#         previous_history.end_datetime = datetime.now(timezone.utc)
#         session.commit()

#     # Create the new history record
#     new_history = ConnectionHistory(
#         connection_id=connection_id,
#         host=connection_data.get('host'),
#         port=connection_data.get('port'),
#         login=connection_data.get('login'),
#         password=connection_data.get('password'),
#         name=connection_data.get("name"),
#         description=connection_data.get("description"),
#         connection_type=connection_data.get("connection_type"),
#         start_datetime=datetime.now(timezone.utc)
#     )
#     session.add(new_history)
#     session.commit()

# def create_proxy_history(proxy, session):
#     """Creates a history record for a Proxy."""
#     history = DBProxy(  # Use the main Proxy model for history
#         phone_id=proxy.phone_id,
#         name=proxy.name,
#         auth_token=proxy.auth_token,
#         user_id=proxy.user_id,
#         expiration_date=proxy.expiration_date,
#         #hours_left=proxy.hours_left,
#         tariff_plan=proxy.tariff_plan,
#         tariff_expiration_date=proxy.tariff_expiration_date,
#         tariff_days_left=proxy.tariff_days_left,
#         device_model=proxy.device_model,
#         active=proxy.active,
#         service_name=proxy.service_name,
#         created_at=proxy.created_at,
#         updated_at=proxy.updated_at,
#         service_account_login=proxy.service_account_login
#     )
#     session.add(history)

# def update_connection(connection_id, connection_data):
#     """Updates a ProxyConnection and creates a new ConnectionHistory record 
#     if any relevant connection details have changed.
#     """
#     with database_service.connect() as session:
#         connection = session.query(DBProxyConnection).get(connection_id)

#         if connection:
#             # Check if any relevant fields have changed
#             has_changed = any([
#                 connection.host != connection_data.get('host'),
#                 connection.port != connection_data.get('port'),
#                 connection.login != connection_data.get('login'),
#                 connection.password != connection_data.get('password'),
#                 connection.name != connection_data.get("name"),
#                 connection.description != connection_data.get("description"),
#                 connection.connection_type != connection_data.get("connection_type")
#             ])

#             if has_changed:
#                 # Create a new ConnectionHistory record 
#                 create_connection_history(connection.id, connection_data, session)

#                 # Update the connection with the new data 
#                 for key, value in connection_data.items():
#                     setattr(connection, key, value)

#                 connection.updated_timestamp = datetime.now(timezone.utc)
#                 session.commit() 